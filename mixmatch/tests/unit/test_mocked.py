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


class SessionFixture(fixtures.Fixture):
    """A fixture that mocks get_{sp,local}_session."""
    def _setUp(self):
        def get_local_auth(token):
            return FakeSession(token, self.local_auths[token])

        def get_sp_auth(sp, token, project):
            return FakeSession(self.sp_auths[(sp, token, project)], project)

        def get_projects_at_sp(sp, token):
            if sp in self.sp_projects:
                return self.sp_projects[sp]
            else:
                return []

        self.local_auths = {}
        self.sp_auths = {}
        self.sp_projects = {}
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_sp_auth', get_sp_auth))
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_local_auth', get_local_auth))
        self.useFixture(fixtures.MonkeyPatch(
            'mixmatch.auth.get_projects_at_sp', get_projects_at_sp))

    def add_local_auth(self, token, project):
        self.local_auths[token] = project

    def add_sp_auth(self, sp, token, project, remote_token):
        self.sp_auths[(sp, token, project)] = remote_token

    def add_project_at_sp(self, sp, project):
        if sp in self.sp_projects:
            self.sp_projects[sp].append(project)
        else:
            self.sp_projects[sp] = [project]


class DatabaseFixture(fixtures.Fixture):
    """A fixture that performs each test in a new, blank database."""
    def __init__(self, conf):
        super(DatabaseFixture, self).__init__()
        oslo_db.options.set_defaults(conf, connection="sqlite://")

    def _setUp(self):
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
        self.session_fixture = self.useFixture(SessionFixture())
        self.db_fixture = self.useFixture(DatabaseFixture(conf=CONF))
        self.app = app.test_client()

        # set config values
        self.config_fixture.load_raw_values(
            group='proxy',
            service_providers='default, remote1',
            aggregation=True)
        self.config_fixture.load_raw_values(
            group='sp_default',
            image_endpoint='http://images.local',
            volume_endpoint='http://volumes.local')
        self.config_fixture.load_raw_values(
            group='sp_remote1',
            image_endpoint='http://images.remote1',
            volume_endpoint='http://volumes.remote1')
        more_config()

    def test_download_image(self):
        self.session_fixture.add_local_auth('wewef', 'my_project_id')
        insert(ResourceMapping("images", "6c4ae06e14bd422e97afe07223c99e18",
                               "not-to-be-read", "default"))

        EXPECTED = 'WEOFIHJREINJEFDOWEIJFWIENFERINWFKEWF'
        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            request_headers={'X-AUTH-TOKEN': 'wewef'},
            text=six.u(EXPECTED),
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'wewef',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.data, six.b(EXPECTED))

    def test_download_image_remote(self):
        REMOTE_PROJECT_ID = "319d8162b38342609f5fafe1404216b9"
        LOCAL_TOKEN = "my-local-token"
        REMOTE_TOKEN = "my-remote-token"

        self.session_fixture.add_sp_auth('remote1', LOCAL_TOKEN,
                                         REMOTE_PROJECT_ID, REMOTE_TOKEN)
        insert(ResourceMapping("images", "6c4ae06e14bd422e97afe07223c99e18",
                               REMOTE_PROJECT_ID, "remote1"))

        EXPECTED = 'WEOFIHJREINJEFDOWEIJFWIENFERINWFKEWF'
        self.requests_fixture.get(
            'http://images.remote1/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text=six.u(EXPECTED),
            request_headers={'X-AUTH-TOKEN': REMOTE_TOKEN},
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': LOCAL_TOKEN,
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.data, six.b(EXPECTED))

    def test_download_image_unknown(self):
        self.session_fixture.add_local_auth('wewef', 'my_project_id')

        self.requests_fixture.get(
            'http://images.local/v2/images/'
            '6c4ae06e-14bd-422e-97af-e07223c99e18',
            text="nope.",
            status_code=400,
            request_headers={'X-AUTH-TOKEN': 'wewef'},
            headers={'CONTENT-TYPE': 'application/json'})
        response = self.app.get(
            '/image/v2/images/6c4ae06e-14bd-422e-97af-e07223c99e18',
            headers={'X-AUTH-TOKEN': 'wewef',
                     'CONTENT-TYPE': 'application/json'})
        self.assertEqual(response.status_code, 400)
