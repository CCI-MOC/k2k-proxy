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

from mixmatch.session import db


class TokenCache(db.Model):
    local_token = db.Column(db.String(255), primary_key=True)
    remote_sp = db.Column(db.String(255), nullable=False)
    remote_token = db.Column(db.String(255), nullable=False)
    remote_project = db.Column(db.String(255), nullable=False)

    def __init__(self, local_token, remote_sp, remote_token, remote_project):
        self.local_token = local_token
        self.remote_sp = remote_sp
        self.remote_token = remote_token
        self.remote_project = remote_project


class ResourceMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(60), nullable=False)
    resource_id = db.Column(db.String(255), nullable=False)
    resource_sp = db.Column(db.String(255), nullable=False)

    def __init__(self, resource_type, resource_id, resource_sp):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.resource_sp = resource_sp