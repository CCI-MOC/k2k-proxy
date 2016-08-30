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

from testtools import testcase

from mixmatch import services
from mixmatch.tests.unit import samples


class Response:
    def __init__(self, text):
        self.text = text


class TestServices(testcase.TestCase):
    def setUp(self):
        super(TestServices, self).setUp()
        self.images = {
            'default': Response(json.dumps(samples.IMAGE_LIST_V2)),
            'sp1': Response(json.dumps(samples.IMAGE_LIST_V2_2))
        }
        self.volumes = {
            'default': Response(json.dumps(samples.VOLUME_LIST_V2)),
            'sp1': Response(json.dumps(samples.VOLUME_LIST_V2))
        }

    def test_aggregate_key(self):
        # Aggregate 'images'
        response = json.loads(services.aggregate(self.images, 'images'))
        self.assertEqual(5, len(response['images']))

        # Aggregate 'volumes'
        response = json.loads(services.aggregate(self.volumes, 'volumes'))
        self.assertEqual(2, len(response['volumes']))

    def test_aggregate_limit(self):
        params = {
            'limit': 1
        }
        response = json.loads(services.aggregate(self.images,
                                                 'images',
                                                 params))
        self.assertEqual(1, len(response['images']))

    def test_aggregate_sort_images(self):
        smallest = '941882c5-b992-4fa9-bcba-9d25d2f4e3b8'
        earliest_updated = '781b3762-9469-4cec-b58d-3349e5de4e9c'
        second_earliest_updated = '1bea47ed-f6a9-463b-b423-14b9cca9ad27'
        latest_updated = '61f655c0-4511-4307-a257-4162c87a5130'

        # Sort images by smallest size, ascending
        params = {
            'sort': 'size:asc'
        }
        response = json.loads(services.aggregate(self.images,
                                                 'images',
                                                 params))
        self.assertEqual(response['images'][0]['id'], smallest)

        # Sort images by smallest size, ascending, return only 1
        # Use alternative sort_key, sort_dir keys.
        params = {
            'sort_key': 'size',
            'sort_dir': 'asc',
            'limit': 1
        }
        response = json.loads(services.aggregate(self.images,
                                                 'images',
                                                 params))
        self.assertEqual(response['images'][0]['id'], smallest)
        self.assertEqual(response['next'], smallest)
        self.assertEqual(1, len(response['images']))

        # Sort images by date of last update, ascending
        params = {
            'sort': 'updated_at:asc',
            'limit': 1
        }
        response = json.loads(services.aggregate(self.images,
                                                 'images',
                                                 params))
        self.assertEqual(response['images'][0]['id'], earliest_updated)
        self.assertEqual(response['next'], earliest_updated)
        self.assertEqual(1, len(response['images']))

        # Sort images by date of last update, descending
        params = {
            'sort': 'updated_at:desc',
            'limit': 1
        }
        response = json.loads(services.aggregate(self.images,
                                                 'images',
                                                 params))
        self.assertEqual(response['images'][0]['id'], latest_updated)
        self.assertEqual(response['next'], latest_updated)
        self.assertEqual(1, len(response['images']))

        # Sort images by date of last update, skip the first one
        params = {
            'sort': 'updated_at:asc',
            'limit': 1,
            'marker': earliest_updated
        }
        response = json.loads(services.aggregate(self.images,
                                                 'images',
                                                 params))
        self.assertEqual(response['images'][0]['id'], second_earliest_updated)
        self.assertEqual(response['next'], second_earliest_updated)
        self.assertEqual(1, len(response['images']))
