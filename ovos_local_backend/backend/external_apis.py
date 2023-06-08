import flask

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_config import Configuration
from ovos_local_backend.database import get_device
from ovos_local_backend.utils import dict_to_camel_case, ExternalApiManager


def _get_lang():
    auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
    uid = auth.split(":")[-1]  # this split is only valid here, not selene
    device = get_device(uid)
    if device:
        return device.lang
    return Configuration().get("lang", "en-us")


def _get_units():
    auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
    uid = auth.split(":")[-1]  # this split is only valid here, not selene
    device = get_device(uid)
    if device:
        return device.system_unit
    return Configuration().get("system_unit", "metric")


def _get_latlon():
    auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
    uid = auth.split(":")[-1]  # this split is only valid here, not selene
    device = get_device(uid)
    if device:
        loc = device.location_json
    else:
        loc = Configuration()["location"]
    lat = loc["coordinate"]["latitude"]
    lon = loc["coordinate"]["longitude"]
    return lat, lon


def get_services_routes(app):

    apis = ExternalApiManager()
    @app.route("/" + API_VERSION + '/geolocation', methods=['GET'])
    @noindex
    @requires_auth
    def geolocation():
        address = flask.request.args["location"]
        return apis.geolocate(address)

    @app.route("/" + API_VERSION + '/wolframAlphaSpoken', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_spoken():
        query = flask.request.args.get("input") or flask.request.args.get("i")
        units = flask.request.args.get("units") or _get_units()
        return apis.wolfram_spoken(query, units)

    @app.route("/" + API_VERSION + '/wolframAlphaSimple', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_simple():
        query = flask.request.args.get("input") or flask.request.args.get("i")
        units = flask.request.args.get("units") or _get_units()
        return apis.wolfram_simple(query, units)

    @app.route("/" + API_VERSION + '/wolframAlphaFull', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_full():
        query = flask.request.args.get("input") or flask.request.args.get("i")
        units = flask.request.args.get("units") or _get_units()
        return apis.wolfram_full(query, units)

    @app.route("/" + API_VERSION + '/wa', methods=['GET'])
    @noindex
    @requires_auth
    def wolfie_xml():
        """ old deprecated endpoint with XML results """
        query = flask.request.args["i"]
        units = flask.request.args.get("units") or _get_units()
        return apis.wolfram_xml(query, units)

    @app.route("/" + API_VERSION + '/owm/forecast/daily', methods=['GET'])
    @noindex
    @requires_auth
    def owm_daily_forecast():
        lang = flask.request.args.get("lang") or _get_lang()
        units = flask.request.args.get("units") or _get_units()
        lat, lon = flask.request.args.get("lat"), flask.request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()
        return apis.owm_daily(lat, lon, units, lang)

    @app.route("/" + API_VERSION + '/owm/forecast', methods=['GET'])
    @noindex
    @requires_auth
    def owm_3h_forecast():
        lang = flask.request.args.get("lang") or _get_lang()
        units = flask.request.args.get("units") or _get_units()
        lat, lon = flask.request.args.get("lat"), flask.request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()
        return apis.owm_hourly(lat, lon, units, lang)

    @app.route("/" + API_VERSION + '/owm/weather', methods=['GET'])
    @noindex
    @requires_auth
    def owm():
        lang = flask.request.args.get("lang") or _get_lang()
        units = flask.request.args.get("units") or _get_units()
        lat, lon = flask.request.args.get("lat"), flask.request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()
        return apis.owm_current(lat, lon, units, lang)

    @app.route("/" + API_VERSION + '/owm/onecall', methods=['GET'])
    @noindex
    @requires_auth
    def owm_onecall():
        units = flask.request.args.get("units") or _get_units()
        lang = flask.request.args.get("lang") or _get_lang()
        lat, lon = flask.request.args.get("lat"), flask.request.args.get("lon")
        if not lat or not lon:
            lat, lon = _get_latlon()
        data = apis.owm_onecall(lat, lon, units, lang)
        # Selene converts the keys from snake_case to camelCase
        return dict_to_camel_case(data)

    return app
