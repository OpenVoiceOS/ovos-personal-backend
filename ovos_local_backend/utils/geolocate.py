import flask

from ovos_backend_client.api import GeolocationApi
from ovos_config import Configuration


def get_request_location():
    _cfg = Configuration()
    if not flask.request.headers.getlist("X-Forwarded-For"):
        ip = flask.request.remote_addr
    else:
        # TODO http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html
        ip = flask.request.headers.getlist("X-Forwarded-For")[0]
    if _cfg["server"].get("override_location", False):
        new_location = _cfg["location"]
    elif _cfg["server"].get("geolocate", True):
        new_location = GeolocationApi().get_ip_geolocation(ip)
    else:
        new_location = {}
    return new_location
