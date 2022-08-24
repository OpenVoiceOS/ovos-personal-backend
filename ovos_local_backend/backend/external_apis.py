from flask import request
from ovos_local_backend.session import SESSION as requests
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_local_backend.utils import dict_to_camel_case
from ovos_local_backend.utils.geolocate import geolocate, get_timezone


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
    def wolfie():
        query = request.args["i"]
        units = request.args.get("units") or "metric"
        if units != "metric":
            units = "imperial"

        # not used?
        # https://products.wolframalpha.com/spoken-results-api/documentation/
        lat = str(CONFIGURATION["default_location"]["coordinate"]["latitude"])
        lon = str(CONFIGURATION["default_location"]["coordinate"]["longitude"])
        geolocation = request.args.get("geolocation") or lat + " " + lon

        url = 'http://api.wolframalpha.com/v1/spoken'
        params = {"appid": CONFIGURATION["wolfram_key"],
                  "i": query,
                  "units": units}
        answer = requests.get(url, params=params).text
        return answer

    @app.route("/" + API_VERSION + '/owm/forecast/daily', methods=['GET'])
    @noindex
    @requires_auth
    def owm_daily_forecast():
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        if not request.args.get("q"):
            params["lat"] = request.args.get("lat") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["latitude"])
            params["lon"] = request.args.get("lon") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["longitude"])
        url = "https://api.openweathermap.org/data/2.5/forecast/daily"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/forecast', methods=['GET'])
    @noindex
    @requires_auth
    def owm_3h_forecast():
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        if not request.args.get("q"):
            params["lat"] = request.args.get("lat") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["latitude"])
            params["lon"] = request.args.get("lon") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["longitude"])
        url = "https://api.openweathermap.org/data/2.5/forecast"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/weather', methods=['GET'])
    @noindex
    @requires_auth
    def owm():
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        if not request.args.get("q"):
            params["lat"] = request.args.get("lat") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["latitude"])
            params["lon"] = request.args.get("lon") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["longitude"])
        url = "https://api.openweathermap.org/data/2.5/weather"
        return requests.get(url, params=params).json()

    @app.route("/" + API_VERSION + '/owm/onecall', methods=['GET'])
    @noindex
    @requires_auth
    def owm_onecall():
        params = dict(request.args)
        params["appid"] = CONFIGURATION["owm_key"]
        if not request.args.get("q"):
            params["lat"] = request.args.get("lat") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["latitude"])
            params["lon"] = request.args.get("lon") or \
                            str(CONFIGURATION["default_location"][
                                    "coordinate"]["longitude"])
        url = "https://api.openweathermap.org/data/2.5/onecall"
        data = requests.get(url, params=params).json()
        # Selene converts the keys from snake_case to camelCase
        return dict_to_camel_case(data)

    return app
