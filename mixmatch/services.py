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

from mixmatch import config


def construct_url(service_provider, service_type,
                  version, action, project_id=None):
    conf = config.get_conf_for_sp(service_provider)

    if service_type == 'image':
        endpoint = conf.image_endpoint

        return "%(endpoint)s/%(version)s/%(action)s" % {
            'endpoint': endpoint,
            'version': version,
            'action': os.path.join(*action)
        }
    elif service_type in ['volume', 'volumev2']:
        endpoint = conf.volume_endpoint

        return "%(endpoint)s/%(version)s/%(project)s/%(action)s" % {
            'endpoint': endpoint,
            'version': version,
            'project': project_id,
            'action': os.path.join(*action)
        }


def aggregate(responses, key):
    resource_list = []
    for sp, response in responses.iteritems():
        resources = json.loads(response)
        if type(resources) == dict:
            resource_list += resources[key]

    return json.dumps({key: resource_list})
