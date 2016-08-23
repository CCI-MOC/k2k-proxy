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

    def test_aggregate(self):
        # Aggregate Image
        image_lists = {
            'default': Response(json.dumps(samples.IMAGE_LIST_V2)),
            'sp1': Response(json.dumps(samples.IMAGE_LIST_V2))
        }
        response = json.loads(services.aggregate(image_lists, 'images'))
        self.assertEqual(6, len(response['images']))

        # Aggregate Volumes
        volume_lists = {
            'default': Response(json.dumps(samples.VOLUME_LIST_V2)),
            'sp1': Response(json.dumps(samples.VOLUME_LIST_V2))
        }
        response = json.loads(services.aggregate(volume_lists, 'volumes'))
        self.assertEqual(2, len(response['volumes']))
