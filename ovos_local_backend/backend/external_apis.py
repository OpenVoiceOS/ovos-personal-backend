from flask import request

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.session import SESSION as requests
from ovos_local_backend.utils import dict_to_camel_case
from ovos_local_backend.utils.geolocate import geolocate, get_timezone
from ovos_local_backend.utils.ovos_api import OvosWeather


def _get_lang():
    auth = request.headers.get('Authorization', '').replace("Bearer ", "")
    uid = auth.split(":")[-1]  # this split is only valid here, not selene
    device = DeviceDatabase().get_device(uid)
    if device:
        return device.lang
    return CONFIGURATION.get("lang", "en-us")


def _get_units():
    auth = request.headers.get('Authorization', '').replace("Bearer ", "")
    uid = auth.split(":")[-1]  # this split is only valid here, not selene
    device = DeviceDatabase().get_device(uid)
    if device:
        return device.system_unit
    return CONFIGURATION.get("system_unit", "metric")


def _get_latlon():
    auth = request.headers.get('Authorization', '').replace("Bearer ", "")
    uid = auth.split(":")[-1]  # this split is only valid here, not selene
    device = DeviceDatabase().get_device(uid)
    if device:
        loc = device.location
    else:
        loc = CONFIGURATION["default_location"]
    lat = loc["coordinate"]["latitude"]
    lon = loc["coordinate"]["longitude"]
    return lat, lon


def get_services_routes(app):
    @app.route("/" + API_VERSION + '/geolocation', methods=['GET'])
    @noindex
    @requires_auth
    def geolocation():
        address = request.args["location"]
        data = geolocate(address)
        return {"data": {
            "city": data["city"],
            "country": data["country"],
            "latitude": float(data["lat"]),
            "longitude": float(data["lon"]),
            "region": data["region"],
            "timezone": get_timezone(float(data["lat"]), float(data["lon"]))
        }}

    @app.route("/" + API_VERSION + '/wolframAlphaSpoken', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_spoken():
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/1
        query = request.args["i"]
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        # lat, lon = _get_latlon()
        # geolocation = request.args.get("geolocation") or lat + " " + lon

        url = 'http://api.wolframalpha.com/v1/spoken'
        params = {"appid": CONFIGURATION["wolfram_key"],
                  "i": query,
                  "units": units}
        answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/wolframAlphaSimple', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_simple():
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/1
        query = request.args["i"]
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        # lat, lon = _get_latlon()
        # geolocation = request.args.get("geolocation") or lat + " " + lon

        url = 'http://api.wolframalpha.com/v1/simple'
        params = {"appid": CONFIGURATION["wolfram_key"],
                  "i": query,
                  "units": units}
        answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/wolframAlphaFull', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_full():
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/1
        query = request.args["i"]
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        # lat, lon = _get_latlon()
        # geolocation = request.args.get("geolocation") or lat + " " + lon

        url = 'http://api.wolframalpha.com/v2/query'
        params = {"appid": CONFIGURATION["wolfram_key"],
                  "input": query,
                  "output": "json",
                  "units": units}
        answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/wa', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_old():
        """ old deprecated endpoint with XML results """
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/1
        query = request.args["i"]
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        # lat, lon = _get_latlon()
        # geolocation = request.args.get("geolocation") or lat + " " + lon

        url = 'http://api.wolframalpha.com/v2/query'
        params = {"appid": CONFIGURATION["wolfram_key"],
                  "input": query,
                  "output": "xml",
                  "units": units}
        answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/owm/forecast/daily', methods=['GET'])
    @noindex
    @requires_auth
    def owm_daily_forecast():
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/2
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        params["lang"] = request.args.get("lang") or _get_lang()
        params["units"] = request.args.get("units") or _get_units()
        if not request.args.get("q"):
            lat, lon = request.args.get("lat"), request.args.get("lon")
            if not lat or not lon:
                lat, lon = _get_latlon()
            params["lat"], params["lon"] = lat, lon
        url = "https://api.openweathermap.org/data/2.5/forecast/daily"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/forecast', methods=['GET'])
    @noindex
    @requires_auth
    def owm_3h_forecast():
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/2
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        params["lang"] = request.args.get("lang") or _get_lang()
        params["units"] = request.args.get("units") or _get_units()
        if not request.args.get("q"):
            lat, lon = request.args.get("lat"), request.args.get("lon")
            if not lat or not lon:
                lat, lon = _get_latlon()
            params["lat"], params["lon"] = lat, lon
        url = "https://api.openweathermap.org/data/2.5/forecast"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/weather', methods=['GET'])
    @noindex
    @requires_auth
    def owm():
        # TODO ovos_api support blocked by https://github.com/OpenVoiceOS/ovos_api_service/issues/2
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        params["lang"] = request.args.get("lang") or _get_lang()
        params["units"] = request.args.get("units") or _get_units()
        if not request.args.get("q"):
            lat, lon = request.args.get("lat"), request.args.get("lon")
            if not lat or not lon:
                lat, lon = _get_latlon()
            params["lat"], params["lon"] = lat, lon
        url = "https://api.openweathermap.org/data/2.5/weather"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/onecall', methods=['GET'])
    @noindex
    @requires_auth
    def owm_onecall():
        params = {
            "lang": request.args.get("lang") or _get_lang(),
            "units": request.args.get("units") or _get_units()
        }

        lat, lon = request.args.get("lat"), request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()

        if not CONFIGURATION["owm_key"]:
            params["lat"], params["lon"] = lat, lon
            data = OvosWeather().get_weather_onecall(params)
        else:
            params["appid"] = CONFIGURATION["owm_key"]
            if request.args.get("q"):
                params["q"] = request.args.get("q")
            else:
                params["lat"], params["lon"] = lat, lon
            url = "https://api.openweathermap.org/data/2.5/onecall"
            data = requests.get(url, params=params).json()
        # Selene converts the keys from snake_case to camelCase
        return dict_to_camel_case(data)

    return app
