# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from functools import wraps
from flask import Response
import flask
from ovos_config import Configuration


def check_auth(uid, token):
    """This function is called to check if a access token is valid."""
    from ovos_local_backend.database import get_device

    device = get_device(uid)
    if device and device.token == token:
        return True
    return False


def requires_opt_in(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from ovos_local_backend.database import get_device

        auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
        uuid = kwargs.get("uuid") or auth.split(":")[-1]  # this split is only valid here, not selene
        device = get_device(uuid)
        if device and device.opt_in:
            return f(*args, **kwargs)

    return decorated


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # skip_auth option is usually unsafe
        # use cases such as docker or ovos-qubes can not share a identity file between devices
        if not Configuration()["server"].get("skip_auth"):
            auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
            uuid = kwargs.get("uuid") or auth.split(":")[-1]  # this split is only valid here, not selene
            if not auth or not uuid or not check_auth(uuid, auth):
                return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to authenticate with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="NOT PAIRED"'})
        return f(*args, **kwargs)

    return decorated


def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_key = Configuration()["server"].get("admin_key")
        auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
        if not auth or not admin_key or auth != admin_key:
            return Response(
                'Could not verify your access level for that URL.\n'
                'You have to authenticate with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="NOT ADMIN"'})
        return f(*args, **kwargs)

    return decorated


def add_response_headers(headers=None):
    """This decorator adds the headers passed in to the response"""
    headers = headers or {}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = flask.make_response(f(*args, **kwargs))
            h = resp.headers
            for header, value in headers.items():
                h[header] = value
            return resp

        return decorated_function

    return decorator


def noindex(f):
    """This decorator passes X-Robots-Tag: noindex"""
    return add_response_headers({'X-Robots-Tag': 'noindex'})(f)
