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

import time

import requests
from flask import request
from oauthlib.oauth2 import WebApplicationClient

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_local_backend.database.oauth import OAuthTokenDatabase
from ovos_local_backend.utils import nice_json


def get_auth_routes(app):
    oauth_in_progress = {}

    @app.route(f"/{API_VERSION}/auth/token", methods=['GET'])
    @requires_auth
    @noindex
    def token():
        """ device is asking for access token, it was created during auto-pairing
        we simplify things and use a deterministic access token, shared with pairing token
        in selene access token would be refreshed here
        """
        token = request.headers.get('Authorization', '').replace("Bearer ", "")
        uuid = token.split(":")[-1]
        device = {"uuid": uuid,
                  "expires_at": time.time() + 999999999999999999,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route(f"/{API_VERSION}/auth/<oauth_id>/auth_url", methods=['GET'])
    @requires_auth
    @noindex
    def oauth_url(oauth_id):
        """ send auth url to user to confirm authorization,
        once user opens it callback is triggered
        """
        params = dict(request.args)

        oauth_in_progress[oauth_id] = params

        client = WebApplicationClient(params["client_id"])
        params["_client"] = client
        oauth_in_progress[oauth_id] = params

        request_uri = client.prepare_request_uri(
            params["auth_endpoint"],
            redirect_uri=request.base_url + "/auth/callback",
            scope=params["scope"],
        )

        return request_uri, 200

    @app.route(f"/{API_VERSION}/auth/callback/<oauth_id>", methods=['GET'])
    @requires_auth
    @noindex
    def oauth_callback(oauth_id):
        """ user completed oauth, save token to db
        """
        params = dict(request.args)
        code = params["code"]

        data = oauth_in_progress[oauth_id]
        client = data["_client"]
        client_id = data["client_id"]
        client_secret = data["client_secret"]
        token_endpoint = data["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(client_id, client_secret),
        ).json()

        with OAuthTokenDatabase() as db:
            db.add_token(oauth_id, token_response)

        oauth_in_progress.pop(oauth_id)
        return nice_json(params)

    @app.route(f"/{API_VERSION}/device/<uuid>/token/<oauth_id>", methods=['GET'])
    @requires_auth
    @noindex
    def oauth_token(uuid, oauth_id):
        """a device is requesting a token for a previously approved OAuth app"""
        data = OAuthTokenDatabase().get(oauth_id) or {}
        return nice_json(data)

    return app
