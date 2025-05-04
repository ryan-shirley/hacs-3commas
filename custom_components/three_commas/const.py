"""Constants for three_commas."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "three_commas"
ATTRIBUTION = "Data provided by 3commas.io API"

# Config flow constants
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"

# Integration specific constants
BASE_URL = "https://api.3commas.io"
