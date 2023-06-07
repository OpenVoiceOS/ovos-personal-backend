import flask

from ovos_backend_client.api import GeolocationApi
from ovos_local_backend.configuration import CONFIGURATION


def get_request_location():
    if not flask.request.headers.getlist("X-Forwarded-For"):
        ip = flask.request.remote_addr
    else:
        # TODO http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html
        ip = flask.request.headers.getlist("X-Forwarded-For")[0]
    if CONFIGURATION["override_location"]:
        new_location = CONFIGURATION["default_location"]
    elif CONFIGURATION["geolocate"]:
        new_location = GeolocationApi().get_ip_geolocation(ip)
    else:
        new_location = {}
    return new_location
