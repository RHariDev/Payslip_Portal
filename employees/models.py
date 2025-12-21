from django.db import models 

from cloudinary_storage.storage import RawMediaCloudinaryStorage

# Create your models here. 
class Employee(models.Model):
    empno = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.empno} - {self.name}"
    
class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payslips")
    month = models.CharField(max_length=25)
    year = models.IntegerField()
    pdf_file = models.FileField(
        upload_to='payslips/', 
        storage=RawMediaCloudinaryStorage(),  
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payslip for {self.employee.empno} - {self.month}" 
 
    