from ovos_local_backend.session import SESSION as requests
import geocoder
from flask import request
from ovos_local_backend.configuration import CONFIGURATION
from timezonefinder import TimezoneFinder


def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    return tf.timezone_at(lng=longitude, lat=latitude)


def geolocate(address):
    data = {}
    location_data = geocoder.osm(address)
    if location_data.ok:
        location_data = location_data.json
        data["raw"] = location_data
        data["country"] = location_data.get("country")
        data["country_code"] = location_data.get("country_code")
        data["region"] = location_data.get("region")
        data["address"] = location_data.get("address")
        data["state"] = location_data.get("state")
        data["confidence"] = location_data.get("confidence")
        data["lat"] = location_data.get("lat")
        data["lon"] = location_data.get("lng")
        data["city"] = location_data.get("city")

        data["postal"] = location_data.get("postal")
        data["timezone"] = location_data.get("timezone_short")
    return data


def get_request_location():
    if not request.headers.getlist("X-Forwarded-For"):
        ip = request.remote_addr
    else:
        # TODO http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html
        ip = request.headers.getlist("X-Forwarded-For")[0]
    if CONFIGURATION["override_location"]:
        new_location = CONFIGURATION["default_location"]
    elif CONFIGURATION["geolocate"]:
        new_location = ip_geolocate(ip)
    else:
        new_location = {}
    return new_location


def get_location_config(address):
    location = {
        "city": {
            "code": "",
            "name": "",
            "state": {
                "code": "",
                "name": "",
                "country": {
                    "code": "US",
                    "name": "United States"
                }
            }
        },
        "coordinate": {
            "latitude": 37.2,
            "longitude": 121.53
        },
        "timezone": {
            "dstOffset": 3600000,
            "offset": -21600000
        }
    }

    data = geolocate(address)
    location["city"]["code"] = data["city"]
    location["city"]["name"] = data["city"]
    location["city"]["state"]["name"] = data["state"]
    # TODO state code
    location["city"]["state"]["code"] = data["state"]
    location["city"]["state"]["country"]["name"] = data["country"]
    # TODO country code
    location["city"]["state"]["country"]["code"] = data["country"]
    location["coordinate"]["latitude"] = data["lat"]
    location["coordinate"]["longitude"] = data["lon"]

    timezone = get_timezone(data["lat"], data["lon"])
    location["timezone"]["name"] = data["timezone"]
    location["timezone"]["code"] = timezone

    return location


def ip_geolocate(ip=None):
    if not ip or ip in ["0.0.0.0", "127.0.0.1"]:
        ip = requests.get('https://api.ipify.org').text
    fields = "status,country,countryCode,region,regionName,city,lat,lon,timezone,query"
    data = requests.get("http://ip-api.com/json/" + ip,
                        params={"fields": fields}).json()
    region_data = {"code": data["region"], "name": data["regionName"],
                   "country": {
                       "code": data["countryCode"],
                       "name": data["country"]}}
    city_data = {"code": data["city"], "name": data["city"],
                 "state": region_data,
                 "region": region_data}
    timezone_data = {"code": data["timezone"],
                     "name": data["timezone"],
                     "dstOffset": 3600000,
                     "offset": -21600000}
    coordinate_data = {"latitude": float(data["lat"]),
                       "longitude": float(data["lon"])}
    return {"city": city_data,
            "coordinate": coordinate_data,
            "timezone": timezone_data}
