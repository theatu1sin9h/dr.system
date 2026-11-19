"""Central configuration for Linux Doctor."""

APP_NAME = "Linux Doctor"
APP_AUTHOR = "[YOUR NAME]"
APP_TAGLINE = "Know your PC. Understand its health."
APP_VERSION = "1.0.0"
REPOSITORY_URL = "https://github.com/linux-doctor/linux-doctor"
LICENSE_NAME = "MIT"

DEFAULT_SETTINGS = {
    "theme": "system",  # "dark", "light", "system"
    "temperature_unit": "celsius",  # "celsius", "fahrenheit"
    "anonymize_reports": True,
    "check_timeout_seconds": 10,
    "elevated_checks_enabled": False,
    "first_launch_completed": False,
}
