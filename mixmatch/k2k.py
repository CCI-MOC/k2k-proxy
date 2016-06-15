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

import os

from keystoneauth1 import identity
from keystoneauth1 import session

from mixmatch.session import db
from mixmatch import config
from mixmatch import model


def get_sp_auth(service_provider, user_token, local_project_id=None):
    # Use K2K to get a scoped token for the SP
    # For some reason if I authenticate with the PROJECT_ID
    # It doesn't like me

    auth = model.RemoteAuth.query.filter_by(local_token=user_token).first()
    print("Auth: %s" % str(auth))
    if auth is None:
        print("Not cached")
        local_auth = identity.v3.Token(auth_url=config.KEYSTONE_URL,
                                       token=user_token,
                                       project_name='admin',
                                       project_domain_id='default')

        remote_auth = identity.v3.Keystone2Keystone(local_auth,
                                                    service_provider,
                                                    project_name='admin',  # FIXME
                                                    project_domain_id='default')  # FIXME

        remote_session = session.Session(auth=remote_auth)
        auth_ref = remote_auth.get_auth_ref(remote_session)

        endpoint = auth_ref.service_catalog.url_for(service_type='volume')
        remote_project = os.path.basename(endpoint)
        remote_token = auth_ref._auth_token

        auth = model.RemoteAuth(local_token=user_token,
                                service_provider=service_provider,
                                remote_token=remote_token,
                                remote_project=remote_project,
                                endpoint_url=endpoint,
                                )

        db.session.add(auth)
        db.session.commit()

    return auth