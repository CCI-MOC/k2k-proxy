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

import sqlalchemy as sql

from mixmatch import config

from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import models


CONF = config.CONF


class RemoteAuth(models.ModelBase):
    __tablename__ = 'remote_auth'
    id = sql.Column(sql.Integer, primary_key=True)
    local_token = sql.Column(sql.String(255), nullable=False)
    service_provider = sql.Column(sql.String(255), nullable=False)
    remote_token = sql.Column(sql.String(255), nullable=False)
    remote_project = sql.Column(sql.String(255), nullable=False)
    endpoint_url = sql.Column(sql.String(255), nullable=False)

    def __init__(self,
                 local_token,
                 service_provider,
                 remote_token,
                 remote_project,
                 endpoint_url):
        self.local_token = local_token
        self.service_provider = service_provider
        self.remote_token = remote_token
        self.remote_project = remote_project
        self.endpoint_url = endpoint_url


class ResourceMapping(models.ModelBase):
    __tablename__ = 'resource_mapping'
    id = sql.Column(sql.Integer, primary_key=True)
    resource_type = sql.Column(sql.String(60), nullable=False)
    resource_id = sql.Column(sql.String(255), nullable=False)
    resource_sp = sql.Column(sql.String(255), nullable=False)

    def __init__(self, resource_type, resource_id, resource_sp):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.resource_sp = resource_sp


class TestMe(models.ModelBase, models.TimestampMixin):
    __tablename__ = 'test_me'
    metadata = None
    id = sql.Column(sql.Integer, primary_key=True)
    label = sql.Column(sql.String(255))


def insert(entity):
    context = enginefacade.transaction_context()
    with enginefacade.writer.using(context) as session:
        session.add(entity)


# Create the tables
# sql.create_all()
