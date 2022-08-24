import requests
from ovos_utils import ovos_service_api


# TODO - this should go into ovos_utils directly
class OvosWeather:
    def __init__(self):
        self.api = ovos_service_api.OVOSApiService()
        self.api.register_device()

    @property
    def uuid(self):
        return self.api.get_uuid()

    @property
    def headers(self):
        self.api.get_session_challenge()
        return {'session_challenge': self.api.get_session_token(),  'backend': 'OWM'}

    def get_weather_onecall(self, query):
        reqdata = {"lat": query.get("lat"),
                   "lon": query.get("lon"),
                   "units": query.get("units"),
                   "lang": query.get("lang")}
        url = f'https://api.openvoiceos.com/weather/onecall_weather_report/{self.uuid}'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r.json()


if __name__ == "__main__":
    from ovos_local_backend.configuration import CONFIGURATION
    loc = CONFIGURATION["default_location"]
    lat = loc["coordinate"]["latitude"]
    lon = loc["coordinate"]["longitude"]
    units = CONFIGURATION["system_unit"]
    params = {
        "lang": "en-us",
        "lat": lat,
        "lon": lon,
        "units": units
    }

    print(OvosWeather().get_weather_onecall(params))

    params["appid"] = CONFIGURATION["owm_key"]
    url = "https://api.openweathermap.org/data/2.5/onecall"
    data = requests.get(url, params=params).json()
    print(data)