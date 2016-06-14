#   Copyright 2016 Massachusetts Open Cloud
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import copy

from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient.v3 import client
import requests

from mixmatch.session import app
from mixmatch.session import request
from mixmatch import config


def learn_mapping(self, response):
    if response.status_code >= 200 < 300:
        # TODO: add mapping for resource
        pass


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # Get the values from the header
    service_provider = request.headers['MM-SERVICE-PROVIDER']
    user_token = request.headers['X-AUTH-TOKEN']
    project_name = request.headers['MM-PROJECT-NAME']
    project_domain = request.headers['MM-PROJECT-DOMAIN-ID']
    endpoint_type = request.headers['MM-ENDPOINT-TYPE']

    # Use K2K to get a scoped token for the SP
    local_auth = identity.v3.Token(auth_url=config.KEYSTONE_URL,
                                   token=user_token)

    remote_auth = identity.v3.Keystone2Keystone(local_auth,
                                                service_provider,
                                                project_name=project_name,
                                                project_domain_id=project_domain)

    remote_session = session.Session(auth=remote_auth)
    remote_client = client.Client(session=remote_session, interface='public')
    remote_token = remote_client.get_token(remote_session)

    # Get the desired endpoint and recreate the path
    endpoint = remote_client.service_catalog.url_for(service_type=endpoint_type)
    remote_url = endpoint + path

    # Prepare the headers
    request_headers = copy.deepcopy(request.headers)
    request_headers['X-AUTH-TOKEN'] = remote_token

    del(request_headers['MM-SERVICE-PROVIDER'])
    del(request_headers['MM-PROJECT-NAME'])
    del(request_headers['MM-PROJECT-DOMAIN-ID'])
    del(request_headers['MM-ENDPOINT-TYPE'])

    # Issue the request and return the response
    response = None
    if request.method == 'GET':
        response = requests.get(remote_url, headers=request_headers, data=request.data)
    elif request.method == 'PUT':
        response = requests.put(remote_url, headers=request_headers, data=request.data)
    elif request.method == 'POST':
        response = requests.post(remote_url, headers=request_headers, data=request.data)
    elif request.method == 'DELETE':
        response = requests.delete(remote_url, headers=request_headers)

    return response.text

if __name__ == "__main__":
    app.run(port=5001)