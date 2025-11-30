import os

def start_venv():
    # Check if the directory already exists
    if not os.path.exists(".venv-win11"):
        # Create a new virtual environment
        os.system("python -m venv .venv-win11")
        print("Virtual environment created successfully.")
    else:
        print("Virtual environment already exists.")

start_venv()