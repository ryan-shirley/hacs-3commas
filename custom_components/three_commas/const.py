"""Constants for three_commas."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "three_commas"
ATTRIBUTION = "Data provided by 3commas.io API"

# Config flow constants
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"  # Keep for backward compatibility
CONF_PRIVATE_KEY = "private_key"
CONF_AUTH_METHOD = "auth_method"
CONF_USER_MODE = "user_mode"
AUTH_METHOD_HMAC = "hmac"
AUTH_METHOD_RSA = "rsa"
USER_MODE_PAPER = "paper"
USER_MODE_REAL = "real"

# Integration specific constants
BASE_URL = "https://api.3commas.io/public/api"
