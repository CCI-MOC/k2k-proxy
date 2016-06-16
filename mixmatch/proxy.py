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

import os

import requests

from mixmatch.session import app, extensions
from mixmatch.session import request
from mixmatch import k2k
from mixmatch import model


class Request:
    def __init__(self, method, path, headers):
        self.method = method

        self.path = path.split('/')
        self.version = self.path[0]
        self.local_project = self.path[1]
        self.action = self.path[2:]

        self.resource = None
        self.mapping = None
        if len(self.action) > 1:
            self.resource = self.action[1]
            self.mapping = model.ResourceMapping.\
                query.filter_by(resource_type=self.action[0],
                                resource_id=self.resource).first()

        self.headers = headers
        self.local_token = headers['X-AUTH-TOKEN']
        #self.project_name = headers['MM-PROJECT-NAME']
        #self.project_domain_id = headers['MM-PROJECT-DOMAIN-ID']
        #self.endpoint_type = headers['MM-ENDPOINT-TYPE']

        extension_uri = os.path.join(*self.action)
        self.extension = extensions['default']
        if extensions.has_key(extension_uri):
            self.extension = extensions[extension_uri]

        if headers.has_key('MM-SERVICE-PROVIDER'):
            self.service_providers = [headers['MM-SERVICE-PROVIDER']]
        elif self.resource and self.mapping:
            print("Found mapping")
            self.service_providers = [self.mapping.resource_sp]
        else:
            self.service_providers = ['dsvm-sp', 'dsvm-sp2', 'dsvm-sp3']

    def forward(self):
        global text, status
        for sp in self.service_providers:
            print ("Querying: %s" % sp)
            # Authenticate with the remote SP
            auth = k2k.get_sp_auth(sp, self.local_token)

            # Prepare header
            headers = dict()
            headers['X-AUTH-TOKEN'] = auth.remote_token

            remote_url = os.path.join(auth.endpoint_url,
                                      os.path.join(*self.action))

            # Send the request to the SP
            text, status = self._request(remote_url, headers)
            print("Remote URL: %s" % remote_url)
            print(status)

            if status == 200:
                if self.resource and not self.mapping:
                    print("Adding mapping")
                    mapping = model.ResourceMapping(resource_sp=sp,
                                                    resource_id=self.resource,
                                                    resource_type=self.action[0])
                    model.insert(mapping)
                break
        return text, status

    def _request(self, url, headers):
        response = None
        if self.method == 'GET':
            response = requests.get(url, headers=headers, data=request.data)
        elif self.method == 'PUT':
            response = requests.put(url, headers=headers, data=request.data)
        elif self.method == 'POST':
            response = requests.post(url, headers=headers, data=request.data)
        elif self.method == 'DELETE':
            response = requests.delete(url, headers=headers)
        return response.text, response.status_code


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    k2k_request = Request(request.method, path, request.headers)
    return k2k_request.forward()

if __name__ == "__main__":
    app.run(port=5001)