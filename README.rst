====================================
OpenStack Keystone-to-Keystone Proxy
====================================

Proxy Service that will forward REST API requests to a remote service provider
which is federated using Keystone-to-Keystone Federation (K2K).

The proxy learns the location of resources and is able to forward requests to
the correct service provider. This allows OpenStack services to use resources
provided by other federated OpenStack deployments, ex. Nova attach a remote
volume.
