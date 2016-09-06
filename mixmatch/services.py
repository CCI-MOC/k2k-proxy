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
import operator
from six.moves.urllib import parse

from mixmatch import config

CONF = config.CONF


def construct_url(service_provider, service_type,
                  version, action, project_id=None):
    """Construct the full URL for an Openstack API call."""
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


def aggregate(responses, key, params=None, path=None):
    """Combine responses from several clusters into one response."""
    if params:
        limit = int(params.get('limit', 0))
        sort = params.get('sort', None)
        marker = params.get('marker', None)

        sort_key = params.get('sort_key', None)
        sort_dir = params.get('sort_dir', None)

        if sort and not sort_key:
            sort_key, sort_dir = sort.split(':')
    else:
        sort_key = None
        limit = 0
        marker = None

    resource_list = []
    for sp, response in responses.items():
        resources = json.loads(response.text)
        if type(resources) == dict:
            resource_list += resources[key]

    start = 0
    last = end = len(resource_list)

    if key == 'images':
        # By default Glance sorts in descending size order
        if not sort_key:
            sort_key = 'size'
            sort_dir = 'desc'

    if sort_key:
        resource_list = sorted(resource_list,
                               key=operator.itemgetter(sort_key),
                               reverse=_is_reverse(sort_dir))

    if limit != 0:
        if marker:
            # Find the position of the resource with marker id
            # and set the list to start at the one after that.
            for index, item in enumerate(resource_list):
                if item['id'] == marker:
                    start = index + 1
                    break
        end = start + limit

    response = {key: resource_list[start:end]}

    # Inject the pagination URIs
    if start > 0:
        params.pop('marker', None)
        response['start'] = '%s?%s' % (path, parse.urlencode(params))
    if end < last:
        params['marker'] = response[key][-1]['id']
        response['next'] = '%s?%s' % (path, parse.urlencode(params))

    return json.dumps(response)


def _is_reverse(order):
    """Return True if order is asc, False if order is desc"""
    if order == 'asc':
        return False
    elif order == 'desc':
        return True
    else:
        raise ValueError
