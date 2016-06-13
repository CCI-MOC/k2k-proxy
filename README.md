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