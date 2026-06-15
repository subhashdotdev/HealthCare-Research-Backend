import subprocess
import platform


def get_chrome_info():
    chrome_version = get_chrome_version()
    chromedriver_version = get_chromedriver_version()
    chromedriver_path = get_chromedriver_path()

    return {
        "chrome_version": chrome_version,
        "chromedriver_version": chromedriver_version,
        "chromedriver_path": chromedriver_path
    }


def get_chrome_version():
    try:
        result = subprocess.run(['chromium', '--version'], capture_output=True, text=True)
        version = result.stdout.split()[1]
        return version
    except Exception as e:
        return str(e)


def get_chromedriver_version() -> str:
    try:
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        version = result.stdout.split()[1]
        return version
    except Exception as e:
        return str(e)


def get_chromedriver_path():
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['where', 'chromedriver'], capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "ChromeDriver not found in PATH. Please check the installation."
    except Exception as e:
        return f"Error finding ChromeDriver: {str(e)}"

