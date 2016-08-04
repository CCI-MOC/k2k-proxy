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

from oslo_config import cfg

CONF = cfg.CONF

# Proxy
proxy_group = cfg.OptGroup(name='proxy',
                           title='Proxy Config Group')

proxy_opts = [
    cfg.StrOpt('database_uri',
               default='sqlite://',
               help='Database URI')
]

# Keystone
keystone_group = cfg.OptGroup(name='keystone',
                              title='Keystone Config Group')

keystone_opts = [
    cfg.StrOpt('auth_url',
               default='http://localhost:35357/v3',
               help='Keystone AUTH URL'),

    cfg.StrOpt('username',
               default='admin',
               help='Proxy username'),

    cfg.StrOpt('user_domain_id',
               default='default',
               help='Proxy user domain id'),

    cfg.StrOpt('password',
               default='nomoresecrete',
               help='Proxy user password'),

    cfg.StrOpt('project_name',
               default='admin',
               help='Proxy project name'),

    cfg.StrOpt('project_domain_id',
               default='default',
               help='Proxy project domain id')
]


CONF.register_group(proxy_group)
CONF.register_opts(proxy_opts, proxy_group)

CONF.register_group(keystone_group)
CONF.register_opts(keystone_opts, keystone_group)

try:
    CONF(default_config_files=['k2k-proxy.conf'])
except cfg.ConfigFilesNotFoundError:
    try:
        CONF(default_config_files=['etc/k2k-proxy.conf'])
    except cfg.ConfigFilesNotFoundError:
        try:
            CONF(default_config_files=['/etc/k2k-proxy.conf'])
        except cfg.ConfigFilesNotFoundError:
            # Just use the defaults
            pass
