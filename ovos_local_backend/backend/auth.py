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

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.utils import nice_json
from ovos_local_backend.backend.decorators import noindex, requires_auth
from flask import request
import time


def get_auth_routes(app):

    @app.route("/" + API_VERSION + "/auth/token", methods=['GET'])
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

    return app
