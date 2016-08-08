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

from sqlalchemy import Boolean, BigInteger, Column, DateTime, Enum, Float
from sqlalchemy import dialects
from sqlalchemy import ForeignKey, Index, Integer, MetaData, String, Table
from sqlalchemy import Text
from sqlalchemy.types import NullType


def create_tables(migrate_engine):
    meta = MetaData(migrate_engine)
    meta.reflect(migrate_engine)

    meta.bind = migrate_engine

    # Resource Mapping Table
    resource_mapping_columns = [
        Column('id', Integer, primary_key=True),
        Column('resource_type', String(60), nullable=False),
        Column('resource_id', String(255), nullable=False),
        Column('resource_sp', String(255), nullable=False),
    ]

    table = Table('resource_mapping', meta, autoload=True)
    table.create()
