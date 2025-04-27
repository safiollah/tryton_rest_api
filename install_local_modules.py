import os
import subprocess
import sys

# Get the absolute path of the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# List of modules to install relative to the script directory
modules = ["tryton", "trytond", "naiad"]

# Get the Python interpreter executable
python_executable = sys.executable

for module in modules:
    module_path = os.path.join(script_dir, module)
    if os.path.isdir(module_path):
        print(f"Installing {module}...")
        try:
            # Change directory
            os.chdir(module_path)
            # Run pip install using the same Python interpreter
            # Use check=True to raise CalledProcessError if pip fails
            subprocess.run([python_executable, "-m", "pip", "install", "."], check=True, capture_output=True, text=True)
            print(f"{module} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing {module}:")
            print(e.stderr)
            # Optionally, exit the script if an installation fails
            # sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred while installing {module}: {e}")
            # sys.exit(1)
        finally:
            # Change back to the script directory (optional, but good practice)
            os.chdir(script_dir)
    else:
        print(f"Directory not found for module {module}: {module_path}")

print("All local modules processed.") 