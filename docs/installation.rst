============
Installation
============

Install dependencies. ::

    $ pip install -r requirements.txt

The proxy will be set up in one OpenStack installation, called the Identity
Provider, or IdP, and it redirect API calls to either the local services, or
remote services in one of several Service Provider installations (SP).

Configuration
=============
The proxy searches for the configuration file ``k2k-proxy.conf`` in the
current directory, the ``etc/`` directory relative to the current directory or
``/etc/``

A sample configuration file has been provided in the ``etc`` folder of the
source code.

The proxy will substitute the endpoint of the service it is proxying.
Only Cinder and Glance are supported for now.

For each SP, you must have a section in ``k2k-proxy.conf`` which contains the
service provider name (as it is listed in Keystone's service catalog), and the
URI for connecting to the notification messagebus in that OpenStack
installation.  For instance::

    [sp_one]
    sp_name="keystone-sp1"
    messagebus="rabbit://rabbituser:rabbitpassword@192.168.7.20"

Keystone Configuration
----------------------

Keystone maintains the service catalog with information about all the
configured endpoints.

In the IdP, delete and then recreate the endpoint which we will proxy. ::

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
in ``/etc/nova/nova.conf``. So, in the IdP, add the following::

    # /etc/nova/nova.conf
    [glance]
    host=<proxy_host>
    port=<proxy_port>

Cinder Notification
-------------------

Every Cinder must be configured to emit notifications on the messagebus.  So,
in both the IdP and every SP, add the following to
``/etc/cinder/cinder.conf``::

    [oslo_messaging_notifications]
    driver = messaging
    topics = notifications

