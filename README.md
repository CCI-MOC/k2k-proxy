# WIP: K2K-Aware Proxy for OpenStack

Service that will forward the request to a remote service provider using
Keystone 2 Keystone (K2K) Federation.

## Examples
Assume the user wants to query a remote Cinder which is federated via
K2K.

1. The user gets a scoped token from Keystone.
2. The user queries the K2K-Proxy via the same API as they would query
Cinder but providing these additional HTTP Headers:
    
    * SERVICE-PROVIDER: Service Provider ID as registered in Keystone.
    * PROJECT-NAME: Project name to scope the remote token to.
    * PROJECT-DOMAIN: Project domain to scope the remote token to.
    * ENDPOINT-TYPE: Endpoint type to select from the catalog.

3. K2K-Proxy gets a SAML assertion from Keystone.
4. Exchanges it for an unscoped token and scopes it to the user
requested project.
5. Caches the token.
6. Finds a suitable endpoint based on the type specified by the users.
7. Queries the selected remote endpoint with the token at the same path
it received the the request and with the same body and headers, except
the above mentioned four headers.
8. Returns the response as-is to the user.

## Possible Future Enhancements
### Dynamic Learning
REST APIs are very predictable, so we can assume that a GET or PUT request to
`/servers/123` destined for service provider X returns 200, then the resource
of type **server** with id **123** exists on service provider **X**. Thus we
can learn the mapping `{ resource_type: 'server', 'id': 123, sp: 'X' }`.

If we assume that in OpenStack UUIDs are unique across multiple deployments,
we can automatically map the next request for that resource to the correct
service provider, without even knowing the service provider ID. If the user
makes a request for a resource id which hasn't been learnt yet, the proxy
could query all the service providers until it finds it and learns the
mapping.

Thus if the request to attach a volume to Nova was made through the K2K proxy,
we would not have to store the service provider where that specific volume
came from. Furthermore, if the request to create the volume also was made
through the K2K proxy, we would not even have to specify the service provider
where the volume is stored. Therefore making Resource Federation entirely
automatic to the user and services using them.

### Resource Aggregation
The proxy would also allow us to issue the same API call to several service
and aggregate the results across the different service providers, providing
the user with a consistent list of all their resources spread across the
different providers. The proxy could inject the location of the resource into
the response if the user requires that information.

Combining this with the enhancement above, the user can just use the UUID
as returned from the list call, knowing that the request will go to the
correct service provider.

### Service Discovery
The proxy can be paired with a *service discovery* service that publishes the
SLAs and costs of the various service providers. An optimization algorithm
could take a specification (ex. heat template) and use the resources from the
various service providers automatically to optimize and objective function
satisfying the constraints defined by the user.

### Load Balancing
The proxy can be paired with a *load monitoring* service and spread the
resources across multiple service providers in case of high load in one.

### Interpreting Qualified UUIDs
The proxy could automatically parse UUIDs which are qualified with the desired
service provider and learn the mapping.
