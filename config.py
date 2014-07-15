import os
import ee
import json


def _load_asset_ids():
    """Return private EE asset ids as dictionary."""
    path = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'ee_asset_ids.json')
    try:
        return json.loads(open(path, "r").read())
    except:
        return {}

# The URL of the Earth Engine API.
EE_URL = 'https://earthengine.googleapis.com'

# The service account email address authorized by your Google contact.
EE_ACCOUNT = '872868960419@developer.gserviceaccount.com'
#'gfw-apis@appspot.gserviceaccount.com'

# The private key associated with your service account in Privacy Enhanced
# Email format (.pem suffix).  To convert a private key from the RSA format
# (.p12 suffix) to .pem, run the openssl command like this:
# openssl pkcs12 -in downloaded-privatekey.p12 -nodes -nocerts > privatekey.pem
EE_PRIVATE_KEY_FILE = 'privatekey.pem'

# DEBUG_MODE will be True if running in a local development environment.
DEBUG_MODE = ('SERVER_SOFTWARE' in os.environ and
              os.environ['SERVER_SOFTWARE'].startswith('Dev'))


EE_CREDENTIALS = ee.ServiceAccountCredentials(EE_ACCOUNT, EE_PRIVATE_KEY_FILE)

assets = _load_asset_ids()
