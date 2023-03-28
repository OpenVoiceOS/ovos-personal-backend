import enum

import geocoder
from flask import request
from timezonefinder import TimezoneFinder

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.session import SESSION as requests
from ovos_backend_client.api import GeolocationApi


def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    return tf.timezone_at(lng=longitude, lat=latitude)


def get_request_location():
    if not request.headers.getlist("X-Forwarded-For"):
        ip = request.remote_addr
    else:
        # TODO http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html
        ip = request.headers.getlist("X-Forwarded-For")[0]
    if CONFIGURATION["override_location"]:
        new_location = CONFIGURATION["default_location"]
    elif CONFIGURATION["geolocate"]:
        new_location = Geocoder().get_location(ip)
    else:
        new_location = {}
    return Location(new_location)


def get_device_location():
    try:
        location = get_request_location()
    except:
        location = Location(CONFIGURATION["default_location"])
    
    return location.serialize


def ip_geolocate(ip=None):
    if not ip or ip in ["0.0.0.0", "127.0.0.1"]:
        ip = requests.get('https://api.ipify.org').text
    fields = "status,country,countryCode,region,regionName,city,lat,lon,timezone,query"
    data = requests.get("http://ip-api.com/json/" + ip,
                        params={"fields": fields}).json()
    return {
        'city': data.get("city"),
        'state': data.get("region"),
        'country': data.get("country"),
        'country_code': data.get("countryCode"),
        'region': data.get("regionName"),
        'latitude': float(data["lat"]),
        'longitude': float(data["lon"]),
        'tz_short': data.get("timezone")
    }


class GeocoderProviders(str, enum.Enum):
    AUTO = "auto"
    SELENE = "selene"
    OSM = "osm"
    ARCGIS = "arcgis"
    GEOCODE_FARM = "geocode_farm"
    # NOTE - most providers in geopy are non functional
    # the lib seems abandoned, TODO migrate to geopy instead


class Geocoder:
    def __init__(self, provider=None):
        self.provider = provider or \
                        CONFIGURATION["microservices"].get("geolocation_provider") or \
                        GeocoderProviders.AUTO

    @property
    def engine(self):
        if self.provider == GeocoderProviders.OSM or \
                self.provider == GeocoderProviders.AUTO:
            return geocoder.osm
        elif self.provider == GeocoderProviders.ARCGIS:
            return geocoder.arcgis
        elif self.provider == GeocoderProviders.GEOCODE_FARM:
            return geocoder.geocodefarm
        elif self.provider == GeocoderProviders.SELENE:
            cfg = CONFIGURATION["selene"]
            if not cfg["enabled"] or not cfg.get("proxy_geolocation"):
                raise ValueError("Selene selected for geolocation, but it is disabled in config!")
            _url = cfg.get("url")
            _version = cfg.get("version") or "v1"
            _identity_file = cfg.get("identity_file")
            return GeolocationApi(_url, _version, _identity_file).get_geolocation

        raise ValueError(f"Unknown geolocation provider: {self.provider}")

    def _geolocate(self, address):
        location = None
        error = ""
        location_data = self.engine(address)
        if location_data.ok:
            location_data = location_data.json
            if location_data["raw"].get("error"):
                error = location_data["raw"]["error"]
            elif location_data.get("accuracy") == "Unmatchable":
                error = "No results found"
            else:
                location = Location(location_data)

        if not location:
            error = "No results found"
        if error:
            raise RuntimeError(error)
        return location

    def get_location(self, address):

        if self.provider == GeocoderProviders.SELENE:
            return self.engine(address)  # selene proxy, special handling
        
        return self._geolocate(address)


class Location:
    def __init__(self, location_data):
        if not isinstance(location_data, dict):
            raise TypeError
        self._raw = location_data
        # backwards comp
        old_conf = isinstance(location_data.get("city"), dict)

        self.city = location_data["city"]["name"] if old_conf else \
                location_data.get("city") or location_data.get("address")
        self.address = location_data.get("address")
        self.state = location_data["city"]["state"]["name"] if old_conf else \
                location_data.get("state")
        self.country_code = location_data["city"]["state"]["country"]["code"] if old_conf else \
                location_data.get("country_code") 
        self.country = location_data["city"]["state"]["country"]["name"] if old_conf else \
                location_data.get("country")
        self.region = location_data.get("region")
        self.latitude = location_data["coordinates"]["latitude"] if old_conf else \
                location_data.get("latitude") 
        self.longitude = location_data["coordinates"]["longitude"] if old_conf else \
                location_data.get("longitude")
        self.tz_short = location_data["timezone"]["name"] if old_conf else \
                location_data.get("tz_short")
        self.tz_code = location_data.get("tz_code") or get_timezone(self.latitude,
                                                                    self.longitude)
        # data["postal"] = location_data.get("postal")

    @property
    def serialize(self):
        # empty dict
        if not self._raw:
            return self._raw
        return {
            'city': self.city,
            'address': self.address,
            'state': self.state,
            'country': self.country,
            'country_code': self.country_code,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'tz_short': self.tz_short,
            'tz_code': self.tz_code
        }
    
    @property
    def old_conf(self):
        return {
            "city": {
                "code": self.city,
                "name": self.city,
                "state": {
                    "code": self.state,
                    "name": self.state,
                    "country": {
                        "code": self.country_code,
                        "name": self.country
                    }
                }
            },
            "coordinate": {
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "timezone": {
                "code": self.tz_code,
                "name": self.tz_short,
                "dstOffset": 0,
                "offset": 0
            }
        }


def geolocate(address):
    """ Deprecated! use Geocoder().get_location(address) instead"""
    return Geocoder()._geolocate(address)


def get_location_config(address):
    """ Deprecated! use Geocoder().get_location(address) instead"""
    return Geocoder().get_location(address)


if __name__ == "__main__":
    g = Geocoder(GeocoderProviders.OSM)
    print(g.get_location("Lisboa").serialize)

    g = Geocoder(GeocoderProviders.ARCGIS)
    print(g.get_location("Moscow").serialize)

    g = Geocoder(GeocoderProviders.GEOCODE_FARM)
    print(g.get_location("Berlin").serialize)
