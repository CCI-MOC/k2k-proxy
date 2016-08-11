============
Installation
============

Install dependencies. ::

    $ pip install -r requirements.txt


Configuration
=============
The proxy searches for the configuration file ``k2k-proxy.conf`` in the
current directory, the ``etc/`` directory relative to the current directory or
``/etc/``

A sample configuration file has been provided in the ``etc`` folder of the
source code.

The proxy will substitute the endpoint of the service it is proxying.
Only Cinder and Glance are supported for now.

Keystone Configuration
----------------------
Keystone maintains the service catalog with information about all the
configured endpoints.

Delete and then recreate the endpoint which we will proxy. ::

    $ openstack endpoint delete <endpoint_id>
    $ openstack endpoint create \
        --publicurl http://<proxy_host>:<proxy_port>/<api_version> \
        --internalurl http://<proxy_host>:<proxy_port>/<api_version> \
        --adminurl http://<proxy_host>:<proxy_port>/<api_version> \
        --region RegionOne \
        <endpoint_type>

Nova Configuration
------------------
Nova reads the endpoint address for glance from the configuration file stored
in ``/etc/nova.conf``. ::

    # /etc/nova.conf
    [glance]
    host=http://<proxy_host>:<proxy_port>

