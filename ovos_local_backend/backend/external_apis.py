from flask import request

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth, check_selene_pairing
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.session import SESSION as requests
from ovos_local_backend.utils import dict_to_camel_case
from ovos_local_backend.utils.geolocate import geolocate, get_timezone
from selene_api.api import GeolocationApi, WolframAlphaApi, OpenWeatherMapApi
from ovos_utils.ovos_service_api import OvosWolframAlpha, OvosWeather

_wolfie = None
_owm = None
if not CONFIGURATION.get("wolfram_key"):
    _wolfie = OvosWolframAlpha()
if not CONFIGURATION.get("owm_key"):
    _owm = OvosWeather()

_selene_cfg = CONFIGURATION.get("selene") or {}
_url = _selene_cfg.get("url")
_version = _selene_cfg.get("version") or "v1"
_identity_file = _selene_cfg.get("identity_file")
_selene_owm = OpenWeatherMapApi(_url, _version, _identity_file)
_selene_wolf = WolframAlphaApi(_url, _version, _identity_file)
_selene_geo = GeolocationApi(_url, _version, _identity_file)


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
    @check_selene_pairing
    @requires_auth
    def geolocation():
        address = request.args["location"]

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_geolocation"):
            data = _selene_geo.get_geolocation(address)
        else:
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
    @check_selene_pairing
    @requires_auth
    def wolfie_spoken():
        query = request.args.get("input") or request.args.get("i")
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_wolfram"):
            answer = _selene_wolf.spoken(query, units, (lat, lon))
        elif _wolfie:
            q = {"input": query, "units": units}
            answer = _wolfie.get_wolfram_spoken(q)
        else:
            url = 'https://api.wolframalpha.com/v1/spoken'
            params = {"appid": CONFIGURATION["wolfram_key"],
                      "i": query,
                      "units": units}
            answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/wolframAlphaSimple', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def wolfie_simple():
        query = request.args.get("input") or request.args.get("i")
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_wolfram"):
            answer = _selene_wolf.simple(query, units, (lat, lon))
        elif _wolfie:
            q = {"input": query, "units": units}
            answer = _wolfie.get_wolfram_simple(q)
        else:
            url = 'https://api.wolframalpha.com/v1/simple'
            params = {"appid": CONFIGURATION["wolfram_key"],
                      "i": query,
                      "units": units}
            answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/wolframAlphaFull', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def wolfie_full():
        query = request.args.get("input") or request.args.get("i")
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_wolfram"):
            answer = _selene_wolf.full_results(query, units, (lat, lon))
        elif _wolfie:
            q = {"input": query, "units": units}
            answer = _wolfie.get_wolfram_full(q)
        else:
            url = 'https://api.wolframalpha.com/v2/query'
            params = {"appid": CONFIGURATION["wolfram_key"],
                      "input": query,
                      "output": "json",
                      "units": units}
            answer = requests.get(url, params=params).json()
        return answer

    @app.route("/" + API_VERSION + '/wa', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def wolfie_old():
        """ old deprecated endpoint with XML results """
        query = request.args["i"]
        units = request.args.get("units") or _get_units()

        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_wolfram"):
            answer = _selene_wolf.full_results(query, units, (lat, lon), {"output": "xml"})
        elif _wolfie:
            q = {"input": query, "units": units, "output": "xml"}
            answer = _wolfie.get_wolfram_full(q)
        else:
            url = 'https://api.wolframalpha.com/v2/query'
            params = {"appid": CONFIGURATION["wolfram_key"],
                      "input": query,
                      "output": "xml",
                      "units": units}
            answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/owm/forecast/daily', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def owm_daily_forecast():
        lang = request.args.get("lang") or _get_lang()
        units = request.args.get("units") or _get_units()
        lat, lon = request.args.get("lat"), request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_weather"):
            return _selene_owm.get_daily((lat, lon), lang, units)

        params = dict(request.args)
        params["lang"] = lang
        params["units"] = units
        if _owm:
            params["lat"], params["lon"] = lat, lon
            return _owm.get_forecast(params).json()

        params["appid"] = CONFIGURATION["owm_key"]
        if not request.args.get("q"):
            params["lat"], params["lon"] = lat, lon
        url = "https://api.openweathermap.org/data/2.5/forecast/daily"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/forecast', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def owm_3h_forecast():
        lang = request.args.get("lang") or _get_lang()
        units = request.args.get("units") or _get_units()
        lat, lon = request.args.get("lat"), request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_weather"):
            return _selene_owm.get_hourly((lat, lon), lang, units)

        params = dict(request.args)
        params["lang"] = lang
        params["units"] = units

        if _owm:
            params["lat"], params["lon"] = lat, lon
            return _owm.get_hourly(params).json()

        if not request.args.get("q"):
            params["lat"], params["lon"] = lat, lon
        params["appid"] = CONFIGURATION["owm_key"]
        url = "https://api.openweathermap.org/data/2.5/forecast"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/weather', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def owm():
        lang = request.args.get("lang") or _get_lang()
        units = request.args.get("units") or _get_units()
        lat, lon = request.args.get("lat"), request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_weather"):
            return _selene_owm.get_current((lat, lon), lang, units)

        params = dict(request.args)
        params["lang"] = lang
        params["units"] = units
        if _owm:
            params["lat"], params["lon"] = lat, lon
            return _owm.get_current(params).json()

        if not request.args.get("q"):
            params["lat"], params["lon"] = lat, lon
        params["appid"] = CONFIGURATION["owm_key"]
        url = "https://api.openweathermap.org/data/2.5/weather"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/onecall', methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def owm_onecall():
        units = request.args.get("units") or _get_units()
        lang = request.args.get("lang") or _get_lang()
        lat, lon = request.args.get("lat"), request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()

        if _selene_cfg.get("enabled") and _selene_cfg.get("proxy_weather"):
            return _selene_owm.get_weather((lat, lon), lang, units)
        elif _owm:
            params = {
                "lang": lang,
                "units": units,
                "lat": lat,
                "lon": lon
            }
            params["lat"], params["lon"] = lat, lon
            return _owm.get_weather_onecall(params).json()
        else:
            params = {
                "lang": lang,
                "units": units,
                "appid": CONFIGURATION["owm_key"]
            }
            if request.args.get("q"):
                params["q"] = request.args.get("q")
            else:
                params["lat"], params["lon"] = lat, lon

            params["appid"] = CONFIGURATION["owm_key"]
            url = "https://api.openweathermap.org/data/2.5/onecall"
            data = requests.get(url, params=params).json()
            # Selene converts the keys from snake_case to camelCase
            return dict_to_camel_case(data)

    return app
