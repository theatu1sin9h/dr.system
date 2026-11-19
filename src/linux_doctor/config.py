"""Central configuration for Dr. System (Linux Doctor)."""

APP_NAME = "Dr. System"
APP_CLI_NAME = "dr-system"
APP_AUTHOR = "Atul Singh Chandel"
APP_AUTHOR_EMAIL = "myself.tas03@gmail.com"
APP_TAGLINE = "Know your PC. Understand its health."
APP_VERSION = "2.5.0"
REPOSITORY_URL = "https://github.com/atulsinghchandel/dr-system"
LICENSE_NAME = "MIT"

DEFAULT_SETTINGS = {
    "theme": "cyber_dark",
    "temperature_unit": "celsius",
    "anonymize_reports": True,
    "check_timeout_seconds": 10,
    "elevated_checks_enabled": False,
}
