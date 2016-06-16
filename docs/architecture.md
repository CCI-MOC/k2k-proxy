# Proxy Architecture

The proxy is designed to substitute an OpenStack endpoint in the service
catalog. Calls received by the proxy will be forwarded to all or select
Keystone to Keystone (K2K) service providers at the same path that they are
received by the proxy.

The proxy defines 3 primitives:

1. Token Mappings (local_token, local_project_id -> service_provider_id ->
remote_token, remote_project_id)

2. Resource Mappings (resource_type, resource_id -> service_provider_id,
resource_endpoint_url)

3. Extensions

## Token Mappings
The proxy receives a call with a specific token scoped to a project. When it
needs to make a call to a service provider endpoint, it will check in the
database if it already contains a mapping matching this token, project,
service provider combination. If it doesn't, it will perform SAML2 exchange
and get a token and store the newly generated mapping.

This can be thought of as a token cache, and in it most basic form it will do
just that.

## Resource Mappings
REST APIs are very predictable, so we can assume that if the proxy receives a
request to `<project_id>/volume/12345` then the user is requesting a resource
of type `volume` with id `12345`. If the proxy doesn't have that specific
mapping, it can flood all the service providers until it receives a 200,
store the newly generated mapping and return the request to the user.

## Extensions
Extensions can be built to register themselves for a specific path. These
extensions can manipulate the request sent to the remote endpoint and also the
response received by the endpoint. Additionally, they can configure where the
request is forwarded.

Example1: The `VolumeAggregator` extensions can register itself for the path
`<project_id>/volumes` and method `GET`. This extensions tells the proxy
to query all service providers. The responses from all the service providers
are parsed by the extension and aggregated. Additionally, the extensions
can also be built to learn the mappings of all the returned responses.

# Use Cases Enabled

## Token Injection
Assume the following architecture: IDP is the Keystone 2 Keystone identity
provider, SP1 is a compute service provider, and SP2 is a block storage
service provider. Alice has a token for the IDP, an instance with id **VM1**
in SP1 and a volume with id **BS1**in SP2. A proxy is running in IDP, a proxy
is sitting in SP1. These proxys intercept the traffic destined for Nova and
Cinder respectively.

Use case: Alice wants to attach BS1 to VM1.

Alice issues the command to Nova, either via the client or dashboard. The
request is sent as:

```
PUT /v2.1/​<project_id>​/servers/​VM1/os-volume_attachments
{
    "volumeAttachment": {
        "volumeId": "BS1",
        "device": "/dev/vdd"
    }
}
```

The proxy knows (or learns) the mapping `server, VM1, SP1`.

An extension in the proxy is registered for that specific path. The proxy
parses the body of the request for the `volumeId` attribute and finds
the mapping `volume, BS1, SP2` (either knows it or learns it). The extension
doesn't change the request body.

Since the proxy already queried SP1 and SP2, it's token mapping table now has:

| LOCAL_TOKEN | LOCAL_PROJECT_ID |  SP | REMOTE_TOKEN | REMOTE_PROJECT_ID |
|-------------|------------------|-----|--------------|-------------------|
| alice_token | alice_project_id | SP1 | SP1_token    | SP1_project_id    |
| alice_token | alice_project_id | SP2 | SP2_token    | SP2_project_id    |

The proxy in the IDP injects the following mappings in the proxy in SP1:

* Token Mapping: SP1_token, SP1_project_id -> SP2 -> SP2_token, SP2_project_id
* Resource Mapping: volume, BS1, SP2, SP2_cinder_url

The proxy in IDP finally forwards the call to the SP2 Nova.

The proxy in SP1 intercepts the call to Cinder, finds the token and resource
mapping previously injected by the other proxy and forwards the request to
the correct endpoint and with the correct token.

Nova is happy, Cinder is happy, Alice is happy.

## Volume create on boot
A particularly tricky case is creating a volume and attaching it on boot.
The previous use case was enabled without any changes to the Nova API or any
of the clients, because the proxy is automatically able to find where the
resources are and correctly route the calls. In this case it is unable to do
so because there is no way to specify where the user wants the volume to be
created.

Thus, we need to modify the client to pass an extra parameter to
`POST <project_id>/servers` with the location for the service provider where
the volume will be created. There is no need to specify the service providers
for the images or volumes which are the source for the creation of this
destination volume.

An extension will register itself to the `POST <project_id>/servers` path.

The extension will parse the service provider location and the block
device mapping information.

The extension will prepare a volume create request for the service provider.
If token injection and resource mapping injection is necessary, it will do
that.

The extension will issue the volume create request and parse the response for
the id of the newly created volume.

The extension will remove the service provider id from the original request
body and modify the block device mapping information to boot from volume id
created in the previous call.

The call will go to Nova, Nova will call back to Cinder, which will be
intercepted by the proxy. The proxy will find or learn the token and
resource mappings (or have them injected) and forward the request to the
correct service provider Cinder endpoint.
