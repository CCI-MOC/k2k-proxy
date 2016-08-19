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

import flask

from mixmatch import config

from mixmatch.ext.base import BaseExtension
from mixmatch.ext.volumes import VolumeAggregator
from mixmatch.ext.images import ImageAggregator
from mixmatch.ext.snapshots import SnapshotAggregator

CONF = config.CONF

app = flask.Flask(__name__)
request = flask.request
