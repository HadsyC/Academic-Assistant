import os
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Deletes migration files, .pyc files, database, runs migrations, and creates a superuser."

    def handle(self, *args, **kwargs):
        # Define the folder(s) to exclude (like .venv)
        exclude_folders = [".venv", "venv"]
        project_root = os.getcwd()  # Get the current working directory

        # Step 1: Delete migration files (except __init__.py) and .pyc files
        for root, dirs, files in os.walk(project_root):
            # Skip excluded folders
            if any(excluded in root for excluded in exclude_folders):
                continue

            if "migrations" in root:
                for file in files:
                    # Delete migration .py files except __init__.py
                    if file != "__init__.py" and file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_root)
                        print(f"Deleting migration file: {relative_path}")
                        os.remove(file_path)

                    # Delete .pyc files
                    if file.endswith(".pyc"):
                        pyc_path = os.path.join(root, file)
                        relative_path = os.path.relpath(pyc_path, project_root)
                        print(f"Deleting .pyc file: {relative_path}")
                        os.remove(pyc_path)

        # Step 2: Delete the SQLite database
        db_path = os.path.join(project_root, "db.sqlite3")
        if os.path.exists(db_path):
            relative_db_path = os.path.relpath(db_path, project_root)
            print(f"Deleting database: {relative_db_path}")
            os.remove(db_path)

        # Step 3: Make migrations and migrate
        print("Running makemigrations...")
        call_command("makemigrations")
        print("Running migrate...")
        call_command("migrate")

        # Step 4: Create superuser
        print("Creating superuser...")
        call_command("createsuperuser", "--noinput")
