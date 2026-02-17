import re
import datetime
import os

CONFIG_FILE = "config.py"
INSTALLER_FILE = "installer.iss"

def get_current_date_str():
    return datetime.datetime.now().strftime("%d%m%Y")

def update_config_version(new_version):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find VERSION = "..."
    pattern = r'VERSION\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)

    if match:
        old_version = match.group(1)
        new_content = content.replace(f'VERSION = "{old_version}"', f'VERSION = "{new_version}"')
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated config.py version: {old_version} -> {new_version}")
    else:
        print("Error: Could not find VERSION in config.py")

def update_installer_version(new_version):
    if not os.path.exists(INSTALLER_FILE):
        print(f"Warning: {INSTALLER_FILE} not found. Skipping installer update.")
        return

    with open(INSTALLER_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Update AppVersion
    app_version_pattern = r'AppVersion=(.+)'
    content = re.sub(app_version_pattern, f'AppVersion={new_version}', content)

    # Update OutputBaseFilename
    # OutputBaseFilename=GtaAsistan_Setup_v1.0.0 -> GtaAsistan_Setup_v17022026.01
    output_filename_pattern = r'OutputBaseFilename=GtaAsistan_Setup_v(.+)'
    content = re.sub(output_filename_pattern, f'OutputBaseFilename=GtaAsistan_Setup_v{new_version}', content)

    with open(INSTALLER_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated installer.iss version to {new_version}")

def calculate_new_version():
    today_str = get_current_date_str()
    
    # Read current version from config.py to determine increment
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'VERSION\s*=\s*"([^"]+)"', content)
        if match:
            current_version = match.group(1)
            # Check if current version matches today's date format
            # Format: ddMMyyyy.number
            parts = current_version.split('.')
            if len(parts) == 2 and parts[0] == today_str:
                # Same day, increment number
                try:
                    new_number = int(parts[1]) + 1
                    return f"{today_str}.{new_number:02d}"
                except ValueError:
                    pass # Fallback to 01
            
            # Different day or invalid format, start fresh
            return f"{today_str}.01"
            
    except Exception as e:
        print(f"Error reading current version: {e}")
    
    return f"{today_str}.01"

if __name__ == "__main__":
    new_version = calculate_new_version()
    print(f"New Version: {new_version}")
    
    update_config_version(new_version)
    update_installer_version(new_version)
