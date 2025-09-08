import pandas as pd
from django.core.management.base import BaseCommand
from employees.models import Employee
from datetime import datetime

class Command(BaseCommand):
    help = "Import employees from Excel file into Employee table"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str, help="Path to Excel file")

    def handle(self, *args, **options):
        file_path = options["excel_file"]

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return

        count = 0
        for _, row in df.iterrows():
            try:
                empno = int(row["EMPNO"])
                name = str(row["NAME"]).strip()

                # Handle DOB safely
                dob = row.get("DOB")
                if pd.isna(dob):
                    dob = None
                elif isinstance(dob, str):
                    try:
                        dob = datetime.strptime(dob, "%Y-%m-%d").date()
                    except:
                        dob = None
                elif hasattr(dob, "to_pydatetime"):  # pandas Timestamp
                    dob = dob.to_pydatetime().date()

                # Handle email safely
                email = row.get("EMAIL")
                if pd.isna(email) or str(email).strip().lower() in ["nan", "", "none"]:
                    email = None
                else:
                    email = str(email).strip()

                # Handle phone safely
                phone = row.get("MOBILE_NO")
                phone = str(int(phone)) if pd.notna(phone) else None

                Employee.objects.update_or_create(
                    empno=empno,
                    defaults={
                        "name": name,
                        "dob": dob,
                        "email": email,
                        "phone": phone,
                    }
                )
                count += 1
            except Exception as e:
                self.stderr.write(self.style.WARNING(
                    f"Skipping row {row.to_dict()} due to error: {e}"
                ))

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} employees"))
