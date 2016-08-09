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

import json
import os

import requests

from mixmatch.config import LOG
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
        if len(self.action) > 1 and self.action[1] != "detail":
            self.resource = self.action[1]
            self.mapping = model.ResourceMapping.find(
                resource_type=self.action[0],
                resource_id=self.resource)
            self.aggregate = False
        else:
            self.aggregate = True

        self.headers = headers
        self.local_token = headers['X-AUTH-TOKEN']
        LOG.info('Local Token: %s ' % self.local_token)

        extension_uri = os.path.join(*self.action)
        self.extension = extensions['default']
        if extensions.has_key(extension_uri):
            self.extension = extensions[extension_uri]

        if headers.has_key('MM-SERVICE-PROVIDER'):
            self.service_providers = [headers['MM-SERVICE-PROVIDER']]
        elif self.resource and self.mapping:
            LOG.info('Found mapping: %s' % self.mapping)
            self.service_providers = [self.mapping.resource_sp]
        else:
            self.service_providers = ['default', 'dsvm-sp', 'dsvm-sp2', 'dsvm-sp3']

    def forward(self):
        responses = dict()
        text = None
        status = None
        for sp in self.service_providers:
            print ("Querying: %s" % sp)
            # Prepare header
            headers = dict()
            if sp is 'default':
                headers['X-AUTH-TOKEN'] = self.local_token
                remote_url = "http://localhost:8776/%s/%s/%s" % (self.version,
                                                                 self.local_project,
                                                                 os.path.join(*self.action))
            else:
                auth = k2k.get_sp_auth(sp, self.local_token)
                headers['X-AUTH-TOKEN'] = auth.remote_token
                remote_url = os.path.join(auth.endpoint_url,
                                          os.path.join(*self.action))


            # Send the request to the SP
            text, status = self._request(remote_url, headers)
            print("Path: %s" % self.path)
            print(self.action)
            print("Remote URL: %s" % remote_url)
            print(status)
            print(request.data)

            responses[sp] = text

            if status >= 200 and status < 300 and not self.aggregate:
                if self.resource and not self.mapping:
                    mapping = model.ResourceMapping(resource_sp=sp,
                                                    resource_id=self.resource,
                                                    resource_type=self.action[0])
                    LOG.info('Adding mapping: %s' % mapping)
                    model.insert(mapping)
                break

        if self.aggregate:
            if extensions.has_key(self.action[0]):
                text = extensions[self.action[0]].aggregate(responses)
            else:
                text = extensions['default'].aggregate(responses)
            status = 200

        return text, status

    def _request(self, url, headers):
        response = None
        if self.method == 'GET':
            response = requests.get(url, headers=headers, data=request.data)
        elif self.method == 'PUT':
            response = requests.put(url, headers=headers, data=request.data)
        elif self.method == 'POST':
            response = requests.post(url, headers=headers, data=request.data)
            print "POST RESPONSE: " + response.text + " " + str(response.status_code)
        elif self.method == 'DELETE':
            response = requests.delete(url, headers=headers)
        print(self.method)
        return response.text, response.status_code


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    k2k_request = Request(request.method, path, request.headers)
    return k2k_request.forward()


def main():
    test1 = model.ResourceMapping('volume', 'volume1', 'sp1')
    test2 = model.ResourceMapping('volume', 'volume2', 'sp2')
    model.insert(test1)
    model.insert(test2)
    print(model.ResourceMapping.find('volume', 'volume2'))
    app.run(port=5001)

if __name__ == "__main__":
    main()