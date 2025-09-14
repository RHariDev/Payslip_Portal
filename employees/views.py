import calendar
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
            name = form.cleaned_data['name']
            dob = form.cleaned_data['dob']
            # Authenticate employee
            try:
                employee = Employee.objects.get(name=name, dob=dob)
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
    payslips = employee.payslips.all().order_by('-month')

    return render(request, "employees/dashboard.html", {
        "employee": employee,
        "payslips": payslips,
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


from django.core.files.storage import storages
from django.conf import settings
import os 

def storage_check(request):
    storage = storages['default']
    return JsonResponse({
        "storage_backend": str(storage.__class__),
        "cloudinary_url": os.getenv("CLOUDINARY_URL")
    })