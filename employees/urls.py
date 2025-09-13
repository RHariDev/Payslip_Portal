from django.urls import path

from employees import views

urlpatterns = [
    path('login/', views.employee_login, name="login"),
    path('dashboard/', views.employee_dashboard, name="dashboard"),
    path('logout/', views.employee_logout, name="logout"),
    path('upload/', views.upload_dbf, name="upload_dbf"),
    path("check-storage/", views.storage_check, name="check_storage"),
]