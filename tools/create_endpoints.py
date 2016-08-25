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

# The assumptions are:
#
# - Proxy is localhost:5001
# - Those services exist, otherwise it will fail.
# - The user in the conf file has permissions to delete and create endpoints.

from mixmatch import config
from mixmatch import auth

INTERFACES = ['public', 'admin', 'internal']


def main():
    config.load_config()
    config.more_config()

    client = auth.get_client()

    host = 'http://localhost:5001'

    # Image
    service = client.services.list(type='image')[0]
    endpoints = client.endpoints.list(service=service)
    for endpoint in endpoints:
        client.endpoints.delete(endpoint)

    for interface in INTERFACES:
        client.endpoints.create(service,
                                '%s/image' % host,
                                interface=interface,
                                region='RegionOne',
                                enabled=True)

    # Volume V1
    service = client.services.list(type='volume')[0]
    endpoints = client.endpoints.list(service=service)
    for endpoint in endpoints:
        client.endpoints.delete(endpoint)

    for interface in INTERFACES:
        client.endpoints.create(service,
                                '%s/volume/v1/$(project_id)s' % host,
                                interface=interface,
                                region='RegionOne',
                                enabled=True)

    # Volume V2
    service = client.services.list(type='volumev2')[0]
    endpoints = client.endpoints.list(service=service)
    for endpoint in endpoints:
        client.endpoints.delete(endpoint)

    for interface in INTERFACES:
        client.endpoints.create(service,
                                '%s/volume/v2/$(project_id)s' % host,
                                interface=interface,
                                region='RegionOne',
                                enabled=True)


if __name__ == "__main__":
    main()
