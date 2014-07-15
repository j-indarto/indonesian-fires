import ee
import os


def init():
    path = os.path.join(os.path.abspath(
        os.path.dirname('__file__')), 'privatekey.pem')
    ee.Initialize(ee.ServiceAccountCredentials(
        '872868960419@developer.gserviceaccount.com', path))
