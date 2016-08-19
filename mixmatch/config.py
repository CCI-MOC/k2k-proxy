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

from os import path

from oslo_config import cfg
from oslo_log import log
from oslo_cache import core as cache

LOG = log.getLogger('root')

CONF = cfg.CONF

# Proxy
proxy_group = cfg.OptGroup(name='proxy',
                           title='Proxy Config Group')

proxy_opts = [
    cfg.IntOpt('port',
               default=5001,
               help='Web Server Port'),

    cfg.ListOpt('service_providers',
                default=None,
                help='List of service providers'),

    cfg.StrOpt('volume_endpoint',
               help='Local Volume Endpoint'),

    cfg.StrOpt('image_endpoint',
               help='Local Image Endpoint'),

    cfg.BoolOpt('search_by_broadcast',
                help='Search All Service Providers on Unknown Resource ID'),

    cfg.BoolOpt('aggregation',
                default=False,
                help='Enable Aggregation when listing resources.'),

    cfg.BoolOpt('caching',
                default=False,
                help='Enable token caching using oslo.cache'),

    cfg.IntOpt('cache_time',
               default=600,
               help='How long to store cached tokens for')
]

# Oslo.Cache
cache.configure(CONF)
token_cache_region = cache.create_region()
cache.configure_cache_region(CONF, token_cache_region)
MEMOIZE_TOKEN = cache.get_memoization_decorator(
    CONF, token_cache_region, "proxy")

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

log.register_options(CONF)

conf_files = [f for f in ['k2k-proxy.conf',
                          'etc/k2k-proxy.conf',
                          '/etc/k2k-proxy.conf'] if path.isfile(f)]

if conf_files is not []:
    CONF(default_config_files=conf_files)

    if CONF.proxy.service_providers:
        for service_provider in CONF.proxy.service_providers:

            sp_group = cfg.OptGroup(name='sp_%s' % service_provider,
                                    title=service_provider)
            sp_opts = [
                cfg.StrOpt('sp_name',
                           default="LOCAL",
                           help='Name of SP in Keystone Catalog.'),
                cfg.StrOpt('messagebus',
                           help='URI to connect to message bus'),
            ]

            CONF.register_group(sp_group)
            CONF.register_opts(sp_opts, sp_group)

log.setup(CONF, 'demo')
