from mixmatch.config import CONF, LOG

from mixmatch.model import insert, delete, ResourceMapping

import oslo_messaging

import eventlet

eventlet.monkey_patch()


class VolumeCreateEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^volume.*',
            event_type='^volume.create.start$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating volume mapping %s -> %s at %s' % (
                payload['volume_id'],
                payload['tenant_id'],
                "LOCAL"))
        insert(ResourceMapping("volume",
                payload['volume_id'],
                payload['tenant_id'],
                "LOCAL"))

class VolumeDeleteEndpoint(object):
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^volume.*',
            event_type='^volume.delete.end$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting volume mapping %s -> %s at %s' % (
                payload['volume_id'],
                payload['tenant_id'],
                "LOCAL"))
        delete(ResourceMapping.find("volume", payload['volume_id']))


endpoints = [VolumeCreateEndpoint(), VolumeDeleteEndpoint()]
transport = oslo_messaging.get_notification_transport(CONF)
targets = [oslo_messaging.Target(topic='notifications')]

server = oslo_messaging.get_notification_listener(transport, targets, endpoints, executor='eventlet')

if __name__=="__main__":
    LOG.info("Now listening for changes")
    server.start()
    while True:
        eventlet.sleep(5) #XXX do something moderately more intelligent than this...
