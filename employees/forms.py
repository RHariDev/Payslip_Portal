from django import forms
from .models import Payslip

class EmployeeLoginForm(forms.Form):
    name = forms.CharField(max_length=100, label="Full Name")
    dob = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date of Birth"
    )

class PayslipUploadForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = ['employee', 'month', 'year', 'pdf_file']
