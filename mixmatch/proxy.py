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

        # Don't stream response by default
        self.stream = False

        self.request_path = path.split('/')
        self.version = self.request_path[0]
        if self.request_path[1] in GLANCE_APIS:
            # Image API calls look like
            # /{version}/{action}
            self.service_type = 'image'
            self.local_project = None
            self.action = self.request_path[1:]

            # Downloading an image requires streaming!
            # If Image API v1, always stream for now
            # This is because the download call in v2 is /file
            # but in v1 is just /images/<image_id> which is very
            # hard to distinguish.
            if 'file' in self.action:
                self.stream = True
            if self.version == 'v1' and self.method == 'GET' \
                    and len(self.action) == 2:
                self.stream = True
        else:
            # Volume API calls look like
            # /{version}/{project_id}/{action}
            self.local_project = self.request_path[1]
            self.action = self.request_path[2:]
            if self.version == 'v1':
                self.service_type = 'volume'
            else:
                self.service_type = 'volumev2'

        self.resource_id = None
        self.mapping = None
        self.aggregate = False
        if len(self.action) > 1 and self.action[1] != "detail":
            self.resource_id = self.action[1]
            self.mapping = model.ResourceMapping.find(
                resource_type=self.action[0],
                resource_id=self.resource_id.replace("-", ""))
        else:
            if self.method == 'GET':
                # We don't want to create stuff everywhere!
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
                if self.mapping:
                    # Which we already know the location of, use that SP.
                    self.service_providers = [self.mapping.resource_sp]
                else:
                    # We don't know about the location of this resource.
                    if CONF.proxy.search_by_broadcast:
                        # But searching is enabled, ask all enabled SPs.
                        self.service_providers = CONF.proxy.service_providers
                    else:
                        # Searching is not enabled, just ask local.
                        self.service_providers = CONF.proxy.service_providers[:1]
            else:
                # We're not looking for a specific Resource.
                if CONF.proxy.aggregation and self.aggregate:
                    # If aggregation is enabled, ask all.
                    self.service_providers = CONF.proxy.service_providers
                else:
                    # Just ask local.
                    self.service_providers = CONF.proxy.service_providers[:1]

    def forward(self):
        responses = dict()
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

                elif self.service_type in ['volume', 'volumev2']:
                    remote_url = "%(endpoint)s/%(version)s/" \
                                 "%(project)s/%(action)s" % {
                                     'endpoint': CONF.proxy.volume_endpoint,
                                     'version': self.version,
                                     'project': self.local_project,
                                     'action': os.path.join(*self.action)
                    }
            else:
                remote_project_id = None
                if self.mapping:
                    remote_project_id = self.mapping.tenant_id
                auth = k2k.get_sp_auth(sp,
                                       self.local_token,
                                       self.service_type,
                                       remote_project_id)
                headers['X-AUTH-TOKEN'] = auth.remote_token

                # The glance endpoint from the service catalog is missing
                # the API version.
                endpoint_url = auth.endpoint_url
                if self.service_type == 'image':
                    endpoint_url += '/' + self.version

                remote_url = os.path.join(endpoint_url,
                                          os.path.join(*self.action))

            # Send the request to the SP
            response = self._request(remote_url, headers)
            responses[sp] = response

            LOG.info("Remote URL: %s, Status: %s, Data: %s" %
                     (remote_url, response.status_code, str(request.data)))

            # If we're looking for a specific resource and we found it
            if 200 <= response.status_code < 300 and self.resource_id:
                break

        # If the request is for listing images or volumes
        # Merge the responses from all service providers into one response.
        if self.aggregate:
            if extensions.has_key(self.action[0]):
                text = extensions[self.action[0]].aggregate(responses)
            else:
                text = extensions['default'].aggregate(responses)
            return flask.Response(
                text,
                200,
                content_type=response.headers['content-type']
            )

        if not self.stream:
            final_response = flask.Response(
                response.text,
                response.status_code
            )
            for key, value in response.headers.iteritems():
                final_response.headers[key] = value
        else:
            final_response = flask.Response(
                flask.stream_with_context(stream_response(response)),
                content_type=response.headers['content-type']
            )
        return final_response

    def _request(self, url, headers):
        response = requests.request(method=self.method,
				    url=url,
                                    headers=headers,
                                    data=request.data,
                                    stream=self.stream)
        return response


@app.route('/', defaults={'path': ''}, methods=['GET','POST', 'PUT',
                                                'DELETE', 'HEAD', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT',
                                    'DELETE', 'HEAD', 'PATCH'])
def proxy(path):
    k2k_request = Request(request.method, path, request.headers)
    return k2k_request.forward()


def main():
    app.run(port=5001, threaded=True)

if __name__ == "__main__":
    main()
