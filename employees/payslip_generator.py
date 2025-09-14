import os
import io
import calendar
from fpdf import FPDF
from dbfread import DBF
import pandas as pd
from django.core.files.base import ContentFile
from .models import Employee, Payslip

class PayslipPDF(FPDF):
    def __init__(self, month_name, year):
        super().__init__()
        self.month_name = month_name
        self.year = year

    def header(self):
        self.set_font("Courier", "B", 16)
        self.cell(0, 10, "ST.JOSEPH'S HIGHER SECONDARY SCHOOL, CUDDALORE-1", ln=True, align="C")
        self.set_font("Courier", "B", 14)
        self.cell(0, 10, f"Payslip for {self.month_name} {self.year}", ln=True, align="C")
        self.ln(2.5)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2.5)

    def generate_body(self, data):
        self.set_font("Courier", "", 12)
        self.cell(100, 10, f"Name: {data['name']}")
        self.cell(0, 10, f"Pay: {data['pay']}", ln=True, align="R")

        self.cell(50, 10, f"Basic: {data['basic']}")
        self.cell(50, 10, f"DA: {data['da']}")
        self.cell(0, 10, f"OA: {data['oa']}", ln=True)

        if (data['days'] != "-"):
            self.cell(63, 10, f"{data['days']} days salary", ln=True)

        info_table = data.get("info_table", [])
        for i in range(0, len(info_table), 2):
            label1, value1 = info_table[i]
            text1 = f"{label1:<15} : {value1:>3}"

            if i + 1 < len(info_table):
                label2, value2 = info_table[i + 1]
                text2 = f"{label2:<17} : {value2:>3}"
            else:
                text2 = ""

            self.cell(95, 8, text1, border=0)
            self.cell(95, 8, text2, border=0, ln=True)

        self.set_x(110)
        self.cell(0, 8, f"Deductions: {data['total_deductions']}", ln=True, align="R")
        self.set_x(110)
        self.cell(0, 8, f"Net Pay: {data['net_pay']}", ln=True, align="R")

        self.ln(2.5)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2.5)


def extract_employee_data(row):
    def parse_amount(val):
        try:
            return int(float(str(val).replace(",", "").strip()))
        except (ValueError, TypeError):
            return 0

    def format_amount(val):
        return f"{val:,}" if val else "-"

    pay = parse_amount(row.get("GROSS"))
    basic = parse_amount(row.get("BASIC_P"))
    da = parse_amount(row.get("DA_P"))
    oa = parse_amount(row.get("SPPAY_P"))
    days = parse_amount(row.get("DAYS"))

    deduction_items = [
        ("P.F", row.get("PF")),
        ("Teacher's Loan 1", row.get("TEACH")),
        ("Paddy Loan", row.get("PADDY")),
        ("Teacher's Loan 2", row.get("TEACH2")),
        ("T.R.F", row.get("MADURA_2")),
        ("Teacher's Loan 3", row.get("TEACH3")),
        ("Tour", row.get("TOUR")),
        ("Teacher's Loan 4", row.get("TEACH4")),
        ("PMSSS", row.get("XX")),
        ("Church Contri.", row.get("CHURCH")),
        ("Mess Deduction", row.get("MESS")),
        ("ESIC", row.get("MADURA_1")),
        ("OD Recovered", None),
        ("Arrear", row.get("ARREAR")),
    ]

    total_deductions = sum(parse_amount(value) for _, value in deduction_items)
    net_pay = pay - total_deductions

    formatted_info_table = []
    for label, value in deduction_items:
        display = format_amount(parse_amount(value))
        formatted_info_table.append((label, display))

    return {
        "name": row.get("NAME", "-") or "-",
        "pay": format_amount(pay),
        "basic": format_amount(basic),
        "da": format_amount(da),
        "oa": format_amount(oa),
        "days": format_amount(days),
        "total_deductions": format_amount(total_deductions),
        "net_pay": format_amount(net_pay),
        "info_table": formatted_info_table
    }


def generate_and_store_payslips(dbf_path, month, year):
    """Generate payslips from DBF and save to DB instead of disk"""
    table = DBF(dbf_path, load=True, encoding='utf-8')
    df = pd.DataFrame(iter(table))
    month_name = calendar.month_name[int(month)]

    generated = 0
    failed = []

    # --- 1. Preload all employees in a dict (one query)
    empnos = df["EMPNO"].astype(str).str.strip().tolist()
    employees = Employee.objects.in_bulk(empnos, field_name="empno")

    # --- 2. Preload existing payslips for this month/year
    existing = Payslip.objects.filter(
        employee__empno__in=empnos, month=month_name, year=year
    ).select_related("employee")
    existing_map = {p.employee.empno: p for p in existing}

    # new_payslips = []  # collect payslips to bulk_create
    
    for _, row in df.iterrows():
        empno = str(row["EMPNO"]).strip()
        emp_data = extract_employee_data(row)

        pdf = PayslipPDF(month_name, year)
        pdf.add_page()
        pdf.generate_body(emp_data)

        pdf_bytes = pdf.output(dest="S").encode("latin1")  # Get PDF as bytes

        employee = employees.get(empno)
        if not employee:
            failed.append(empno)
            continue  # Skip if employee not in system

        payslip = existing_map.get(empno)
        if payslip:
            # Update existing payslip
            payslip.pdf_file.save(
                f"payslip_{empno}_{month}{year}.pdf", 
                ContentFile(pdf_bytes), 
            )
        else:
            # Create new payslip instance
            payslip = Payslip(
                employee=employee,
                month=month_name,
                year=year,
            )
            payslip.pdf_file.save(
                f"payslip_{empno}_{month}{year}.pdf", 
                ContentFile(pdf_bytes), 
            )
            # new_payslips.append(payslip)

        generated += 1
        
    # if new_payslips:
    #     Payslip.objects.bulk_create(new_payslips)

    return { 
        "count": generated,
        "failed": failed 
    }
