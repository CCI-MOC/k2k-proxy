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
import flask

from mixmatch.config import LOG, CONF
from mixmatch.session import app, extensions
from mixmatch.session import request
from mixmatch import k2k
from mixmatch import model

GLANCE_APIS = ['images', 'schemas', 'metadefs', 'tasks']


def stream_response(response):
    yield response.raw.read()


class Request:
    def __init__(self, method, path, headers):
        self.method = method
        self.headers = headers

        self.request_path = path.split('/')
        self.version = self.request_path[0]
        if self.request_path[1] in GLANCE_APIS:
            # Image API calls look like
            # /{version}/{action}
            self.service_type = 'image'
            self.local_project = None
            self.action = self.request_path[1:]
        else:
            # Volume API calls look like
            # /{version}/{project_id}/{action}
            self.local_project = self.request_path[1]
            self.action = self.request_path[2:]
            if self.version == 'v1':
                self.service_type = 'volume'
            else:
                self.service_type = 'volumev2'

        # Don't stream response by default
        self.stream = False

        self.resource_id = None
        self.mapping = None
        if len(self.action) > 1 and self.action[1] != "detail":
            self.resource_id = self.action[1]
            self.mapping = model.ResourceMapping.find(
                resource_type=self.action[0],
                resource_id=self.resource_id)
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
            # The user wants a specific service provider, use that SP.
            self.service_providers = [headers['MM-SERVICE-PROVIDER']]
        else:
            if self.resource_id:
                # The user is looking for a specific resource.
                if __name__ == '__main__':
                    if self.mapping:
                        # Which we already know the location of, use that SP.
                        self.service_providers = [self.mapping.resource_sp]
                    else:
                        # We don't know about the location of this resource.
                        if CONF.proxy.search_by_broadcast:
                            # But searching is enabled, ask all enabled SPs.
                            self.service_providers = CONF.proxy.service_providers
                        else:
                            # Searching is not enabled, return 404
                            flask.abort(404)
            else:
                # We're not looking for a specific Resource, ask all.
                self.service_providers = CONF.proxy.service_providers

    def forward(self):
        responses = dict()
        text = None
        status = None
        for sp in self.service_providers:
            print ("Querying: %s" % sp)
            # Prepare header
            headers = dict()
            headers["Accept"] = "application/json"
            headers["Content-Type"] = "application/json"
            if sp == 'default':
                headers['X-AUTH-TOKEN'] = self.local_token

                if self.service_type == 'image':
                    remote_url = "%(endpoint)s/%(version)s/%(action)s" % {
                                    'endpoint': CONF.proxy.image_endpoint,
                                    'version': self.version,
                                    'action': os.path.join(*self.action)
                    }

                    # Downloading an image requires streaming!
                    # If Image API v1, always stream for now
                    # This is because the download call in v2 is /file
                    # but in v1 is just /images/<image_id>
                    if 'file' in self.action:
                        self.stream = True
                    if self.version == 'v1':
                        self.stream = True
                elif self.service_type in ['volume', 'volumev2']:
                    remote_url = "%(endpoint)s/%(version)s/" \
                                 "%(project)s/%(action)s" % {
                                     'endpoint': CONF.proxy.volume_endpoint,
                                     'version': self.version,
                                     'project': self.local_project,
                                     'action': os.path.join(*self.action)
                    }
            else:
                auth = k2k.get_sp_auth(sp, self.local_token, self.service_type)
                headers['X-AUTH-TOKEN'] = auth.remote_token
                remote_url = os.path.join(auth.endpoint_url,
                                          os.path.join(*self.action))

            # Send the request to the SP
            response = self._request(remote_url, headers)
            print("Path: %s" % self.request_path)
            print(self.action)
            print("Remote URL: %s" % remote_url)
            print(status)
            print(request.data)

            responses[sp] = response

            if status >= 200 < 300 and not self.aggregate:
                if self.resource_id and not self.mapping:
                    mapping = model.ResourceMapping(resource_sp=sp,
                                                    resource_id=self.resource_id,
                                                    resource_type=self.action[0])
                    LOG.info('Adding mapping: %s' % mapping)
                    model.insert(mapping)
                break

        # If the request is for listing images or volumes
        # Merge the responses from all service providers into one response.
        if self.aggregate:
            if extensions.has_key(self.action[0]):
                text = extensions[self.action[0]].aggregate(responses)
            else:
                text = extensions['default'].aggregate(responses)
            status = 200
            return text, status

        if not self.stream:
            return flask.Response(
                response.text,
                response.status_code,
                content_type=response.headers['content-type']
            )
        else:
            return flask.Response(
                flask.stream_with_context(stream_response(response)),
                content_type=response.headers['content-type']
            )

    def _request(self, url, headers):
        # If ending with /, strip it
        if url[-1] == '/':
            url = url[:-1]

        response = None
        if self.method == 'GET':
            response = requests.get(url,
                                    headers=headers,
                                    data=request.data,
                                    stream=self.stream)
        elif self.method == 'PUT':
            response = requests.put(url,
                                    headers=headers,
                                    data=request.data)
        elif self.method == 'POST':
            response = requests.post(url,
                                     headers=headers,
                                     data=request.data)
        elif self.method == 'DELETE':
            response = requests.delete(url,
                                       headers=headers)
        elif self.method == 'HEAD':
            response = requests.head(url, headers=headers,
                                     data=request.data)

        return response


@app.route('/', defaults={'path': ''}, methods=['GET','POST', 'PUT',
                                                'DELETE', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT',
                                    'DELETE', 'HEAD'])
def proxy(path):
    k2k_request = Request(request.method, path, request.headers)
    return k2k_request.forward()


def main():
    test1 = model.ResourceMapping('volume', 'volume1', 'proj1', 'sp1')
    test2 = model.ResourceMapping('volume', 'volume2', 'proj2', 'sp2')
    model.insert(test1)
    model.insert(test2)
    print(model.ResourceMapping.find('volume', 'volume2'))
    app.run(port=5001)

if __name__ == "__main__":
    main()
