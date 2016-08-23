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

import six
from testtools import testcase
from requests_mock.contrib import fixture as requests_fixture
from mock import patch
from oslo_config import fixture as config_fixture
import oslo_db
import fixtures

from mixmatch.config import CONF, more_config
from mixmatch.proxy import app
from mixmatch.model import BASE, enginefacade, insert, ResourceMapping


class FakeSession():
    """A replacement for keystoneauth1.session.Session."""
    def __init__(self, token, project):
        self.token = token
        self.project = project

    def get_token(self):
        return self.token

    def get_project_id(self):
        return self.project


class DatabaseFixture(fixtures.Fixture):
    """A fixture that performs each test in a new, blank database."""
    def __init__(self, conf):
        super(DatabaseFixture, self).__init__()
        oslo_db.options.set_defaults(conf, connection="sqlite://")

    def setUp(self):
        super(DatabaseFixture, self).setUp()
        # create_tables()
        context = enginefacade.transaction_context()
        with enginefacade.writer.using(context) as session:
            self.engine = session.get_bind()
        BASE.metadata.create_all(bind=self.engine)
        self.addCleanup(BASE.metadata.drop_all, bind=self.engine)

    def recreate(self):
        BASE.metadata.create_all(bind=self.engine)


class TestMock(testcase.TestCase):
    def setUp(self):
        super(TestMock, self).setUp()
        self.requests_fixture = self.useFixture(requests_fixture.Fixture())
        self.config_fixture = self.useFixture(config_fixture.Config(conf=CONF))
        self.app = app.test_client()

        # set config values
        self.config_fixture.load_raw_values(
            group='proxy',
            service_providers='default')
        self.config_fixture.load_raw_values(
            group='sp_default',
            image_endpoint='http://images.local',
            volume_endpoint='http://volumes.local')
        more_config()

        # Database stuff
        self.db_fixture = self.useFixture(DatabaseFixture(conf=CONF))

        insert(ResourceMapping("volume", "24564325645", "1234234234", "Wefwe"))

    @patch('mixmatch.auth.get_local_auth')
    def test_download_image(self, get_local_auth):
        # mock K2K functionality

        def fake_get_local_auth(user_token):
            return FakeSession(user_token, 'my_project_id')

        get_local_auth.side_effect = fake_get_local_auth

        # set up db

        insert(ResourceMapping("image", "6c4ae06e14bd422e97afe07223c99e18",
                               "default", "not-to-be-read"))

        # mock requests responses

        EXPECTED = 'WEOFIHJREINJEFDOWEIJFWIENFERINWFKEWF'
        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text=six.u(EXPECTED),
            headers={'CONTENT-TYPE': 'application/json'})

        # do the API call

        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X_AUTH_TOKEN': 'wewef',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.data, six.b(EXPECTED))
