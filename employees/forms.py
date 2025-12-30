from django import forms
from .models import Employee, Payslip

class EmployeeLoginForm(forms.Form):
    empno = forms.CharField(max_length=10, label="Employee Number")
    dob = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date of Birth"
    ) 

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['dob', 'email', 'phone'] 

class PayslipUploadForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = ['employee', 'month', 'year', 'pdf_file']
