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

import uuid

import requests
import flask

from mixmatch import config
from mixmatch.config import LOG, CONF
from mixmatch.session import app
from mixmatch.session import chunked_reader
from mixmatch.session import request
from mixmatch import auth
from mixmatch import model
from mixmatch import services


def stream_response(response):
    yield response.raw.read()


def is_valid_uuid(value):
    try:
        uuid.UUID(value, version=4)
        return True
    except ValueError:
        return False


class RequestHandler:
    def __init__(self, method, path, headers):
        self.method = method
        self.headers = headers

        self.request_path = path.split('/')

        # workaround to fix glance requests
        # that does not contain image directory
        if self.request_path[0] in ['v1', 'v2']:
            self.request_path = ['image'] + self.request_path

        self.service_type = self.request_path[0]
        self.version = self.request_path[1]
        if self.service_type == 'image':
            # /image/{version}/{action}
            self.action = self.request_path[2:]
        elif self.service_type == 'volume':
            # /volume/{version}/{project_id}/{action}
            self.action = self.request_path[3:]
        else:
            raise ValueError

        if self.method in ['GET']:
            self.stream = True
        else:
            self.stream = False

        self.resource_id = None
        self.mapping = None
        self.aggregate = False

        if len(self.action) > 1 and is_valid_uuid(self.action[1]):
            self.resource_id = self.action[1]
            self.mapping = model.ResourceMapping.find(
                resource_type=self.action[0],
                resource_id=self.resource_id.replace("-", ""))
        else:
            if self.method == 'GET' \
                    and self.action[0] in ['images', 'volumes', 'snapshots']:
                self.aggregate = True

        self.headers = headers
        self.local_token = headers['X-AUTH-TOKEN']
        LOG.info('Local Token: %s ' % self.local_token)

        if 'MM-SERVICE-PROVIDER' in headers:
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
                        self.service_providers = \
                                CONF.proxy.service_providers[:1]
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
        headers = self._prepare_headers(self.headers)
        for sp in self.service_providers:
            if sp == 'default':
                auth_session = auth.get_local_auth(self.local_token)
            else:
                remote_project_id = None
                if self.mapping:
                    remote_project_id = self.mapping.tenant_id
                auth_session = auth.get_sp_auth(sp,
                                                self.local_token,
                                                remote_project_id)

            headers['X-AUTH-TOKEN'] = auth_session.get_token()

            remote_url = services.construct_url(
                sp,
                self.service_type,
                self.version,
                self.action,
                project_id=auth_session.get_project_id()
            )

            # Send the request to the SP
            response = self._request(remote_url, headers)
            responses[sp] = response

            LOG.info("Remote URL: %s, Status: %s" %
                     (remote_url, response.status_code))

            # If we're looking for a specific resource and we found it
            if 200 <= response.status_code < 300 and self.resource_id:
                break

        # If the request is for listing images or volumes
        # Merge the responses from all service providers into one response.
        if self.aggregate:
            return flask.Response(
                services.aggregate(responses, self.action[0]),
                200,
                content_type=response.headers['content-type']
            )

        if not self.stream:
            final_response = flask.Response(
                response.text,
                response.status_code
            )
            for key, value in response.headers.items():
                final_response.headers[key] = value
        else:
            final_response = flask.Response(
                flask.stream_with_context(stream_response(response)),
                response.status_code,
                content_type=response.headers['content-type']
            )
        return final_response

    def _request(self, url, headers):
        if self.chunked:
            return requests.request(method=self.method,
                                    url=url,
                                    headers=headers,
                                    data=chunked_reader())
        else:
            return requests.request(method=self.method,
                                    url=url,
                                    headers=headers,
                                    data=request.data,
                                    stream=self.stream,
                                    params=request.args)

    @staticmethod
    def _prepare_headers(user_headers):
        headers = dict()
        headers['Accept'] = user_headers.get('Accept', '')
        headers['Content-Type'] = user_headers.get('Content-Type', '')
        for key, value in user_headers.items():
            if key.lower().startswith('x-') and key.lower() != 'x-auth-token':
                headers[key] = value
        return headers

    @property
    def chunked(self):
        return self.headers.get('Transfer-Encoding', '').lower() == 'chunked'


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT',
                                                'DELETE', 'HEAD', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT',
                                    'DELETE', 'HEAD', 'PATCH'])
def proxy(path):
    k2k_request = RequestHandler(request.method, path, request.headers)
    return k2k_request.forward()


def main():
    config.load_config()
    config.more_config()
    model.create_tables()


if __name__ == "__main__":
    main()
    app.run(port=5001, threaded=True)
