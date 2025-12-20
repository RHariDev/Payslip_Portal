import calendar
from datetime import datetime
from django.contrib import messages
import tempfile
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile

from employees.forms import EmployeeLoginForm, PayslipUploadForm
from employees.models import Employee
from employees.payslip_generator import generate_and_store_payslips

# Create your views here.
def employee_login(request):
    if request.method == 'POST':
        form = EmployeeLoginForm(request.POST)
        if form.is_valid():
            empno = form.cleaned_data['empno']
            dob = form.cleaned_data['dob']
            # Authenticate employee
            try:
                employee = Employee.objects.get(empno=empno, dob=dob)
                # Store employee in session
                request.session['employee_id'] = employee.id
                return redirect("dashboard")
            except Employee.DoesNotExist:
                messages.error(request, "Invalid credentials")
    else:
        form = EmployeeLoginForm()

    return render(request, 'employees/login.html', {'form': form}) 

def employee_dashboard(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        return redirect("login")

    employee = Employee.objects.get(id=employee_id)
    payslips = list(employee.payslips.all())

    # --- Define correct month order ---
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # --- Filtering logic ---
    month = request.GET.get('month')
    year = request.GET.get('year')

    if month:
        payslips = [p for p in payslips if p.month == month]
    if year:
        payslips = [p for p in payslips if str(p.year) == str(year)]

    # --- Sort payslips correctly (by year desc, then month order) ---
    payslips.sort(key=lambda p: (p.year, month_order.index(p.month)), reverse=True)

    # --- Prepare dropdown data ---
    current_year = datetime.now().year
    month_range = month_order  # use actual month names for dropdown
    year_range = range(current_year - 5, current_year + 1)

    return render(request, "employees/dashboard.html", {
        "employee": employee,
        "payslips": payslips,
        "month_range": month_range,
        "year_range": year_range,
        "selected_month": month or "",
        "selected_year": year or "",
    }) 

def employee_logout(request):
    request.session.flush()
    return redirect("login")

@staff_member_required
def upload_dbf(request):
    if request.method == "POST":
        dbf_file = request.FILES.get("dbf_file")
        month = request.POST.get("month")
        year = request.POST.get("year")

        if not dbf_file or not month or not year:
            messages.error(request, "Please provide all required fields.")
            return redirect("upload_dbf")

        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dbf") as tmp:
            for chunk in dbf_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        # Call your generator and get result dict
        result = generate_and_store_payslips(tmp_path, month, year)

        # Show messages based on dict
        messages.success(request, f"{result.get('count', 0)} payslips generated successfully!")
        failed_list = result.get('failed', [])
        if failed_list:
            messages.warning(request, f"Failed to generate payslips for: {', '.join(map(str, failed_list))}")

        return redirect("upload_dbf")

    return render(request, "employees/upload_dbf.html")


from django.core.files.storage import default_storage
import os 

def storage_check(request):
    return JsonResponse({
        "storage_backend": str(default_storage.__class__),
        "cloudinary_url": os.getenv("CLOUDINARY_URL")
    }) 
 

# import calendar
# from datetime import datetime
# import tempfile

# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.admin.views.decorators import staff_member_required

# from employees.models import Employee
# from employees.payslip_generator import generate_and_store_payslips


# # ------------------------------------------------------------
# # 1️⃣ EMPLOYEE LOGIN (React)
# # ------------------------------------------------------------
# @csrf_exempt
# def employee_login(request):
#     if request.method != 'POST':
#         return JsonResponse({"error": "Invalid method"}, status=405)

#     empno = request.POST.get('empno')
#     dob = request.POST.get('dob')

#     try:
#         employee = Employee.objects.get(empno=empno, dob=dob)
#         request.session['employee_id'] = employee.id

#         return JsonResponse({
#             "success": True,
#             "employee": {
#                 "name": employee.name,
#                 "empno": employee.empno
#             }
#         })

#     except Employee.DoesNotExist:
#         return JsonResponse({
#             "success": False,
#             "error": "Invalid credentials"
#         }, status=401)


# # ------------------------------------------------------------
# # 2️⃣ FETCH PAYSLOPS (React Dashboard)
# # ------------------------------------------------------------
# def employee_dashboard(request):
#     employee_id = request.session.get('employee_id')

#     if not employee_id:
#         return JsonResponse({"error": "Unauthorized"}, status=401)

#     employee = Employee.objects.get(id=employee_id)
#     payslips = employee.payslips.all().order_by("-year", "-month")

#     # --- Filters ---
#     month = request.GET.get("month")
#     year = request.GET.get("year")

#     if month:
#         payslips = payslips.filter(month=month)

#     if year:
#         payslips = payslips.filter(year=year)

#     month_order = [
#         "January", "February", "March", "April", "May", "June",
#         "July", "August", "September", "October", "November", "December"
#     ]

#     # Manual month sorting
#     payslips = sorted(
#         payslips,
#         key=lambda p: (p.year, month_order.index(p.month)),
#         reverse=True
#     )

#     data = {
#         "employee": {
#             "name": employee.name,
#             "empno": employee.empno,
#         },
#         "payslips": [
#             {
#                 "id": p.id,
#                 "month": p.month,
#                 "year": p.year,
#                 "pdf_url": p.pdf_file.url,
#             }
#             for p in payslips
#         ],
#         "months": month_order,
#         "years": list(range(datetime.now().year - 5, datetime.now().year + 1)),
#     }

#     return JsonResponse(data, safe=False)


# # ------------------------------------------------------------
# # 3️⃣ LOGOUT (React)
# # ------------------------------------------------------------
# def employee_logout(request):
#     request.session.flush()
#     return JsonResponse({"success": True})


# # ------------------------------------------------------------
# # 4️⃣ ADMIN — UPLOAD DBF FILE (React Admin Panel)
# # ------------------------------------------------------------
# @csrf_exempt
# @staff_member_required
# def upload_dbf(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid method"}, status=405)

#     dbf_file = request.FILES.get("dbf_file")
#     month = request.POST.get("month")
#     year = request.POST.get("year")

#     if not dbf_file or not month or not year:
#         return JsonResponse({
#             "success": False,
#             "error": "Missing required fields (dbf_file/month/year)"
#         }, status=400)

#     # Save as temporary file
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".dbf") as tmp:
#         for chunk in dbf_file.chunks():
#             tmp.write(chunk)
#         tmp_path = tmp.name

#     # Process DBF → Generate payslips → Save PDFs
#     result = generate_and_store_payslips(tmp_path, month, year)

#     return JsonResponse({
#         "success": True,
#         "generated": result.get("count", 0),
#         "failed": result.get("failed", []),
#     })
