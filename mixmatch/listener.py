from mixmatch.config import CONF, LOG

from mixmatch.model import insert, delete, ResourceMapping

import oslo_messaging

import eventlet

eventlet.monkey_patch()


class VolumeCreateEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^volume.*',
            event_type='^volume.create.start$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating volume mapping %s -> %s at %s' % (
                payload['volume_id'],
                payload['tenant_id'],
                self.sp_name))
        insert(ResourceMapping("volume",
                payload['volume_id'],
                payload['tenant_id'],
                self.sp_name))

class VolumeDeleteEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^volume.*',
            event_type='^volume.delete.end$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting volume mapping %s -> %s at %s' % (
                payload['volume_id'],
                payload['tenant_id'],
                self.sp_name))
        delete(ResourceMapping.find("volume", payload['volume_id']))

class SnapshotCreateEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^snapshot.*',
            event_type='^snapshot.create.start$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating snapshot mapping %s -> %s at %s' % (
                payload['snapshot_id'],
                payload['tenant_id'],
                self.sp_name))
        insert(ResourceMapping("snapshot",
                payload['snapshot_id'],
                payload['tenant_id'],
                self.sp_name))

class SnapshotDeleteEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^snapshot.*',
            event_type='^snapshot.delete.end$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting snapshot mapping %s -> %s at %s' % (
                payload['snapshot_id'],
                payload['tenant_id'],
                self.sp_name))
        delete(ResourceMapping.find("snapshot", payload['snapshot_id']))

class ImageCreateEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^image.*',
            event_type='^image.create$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Creating image mapping %s -> %s at %s' % (
                payload['id'],
                payload['owner'],
                self.sp_name))
        insert(ResourceMapping("image",
                payload['id'],
                payload['owner'],
                self.sp_name))

class ImageDeleteEndpoint(object):
    def __init__(self, sp_name):
        self.sp_name = sp_name
    filter_rule = oslo_messaging.NotificationFilter(
            publisher_id='^image.*',
            event_type='^image.delete$')
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.info('Deleting image mapping %s -> %s at %s' % (
                payload['id'],
                payload['owner'],
                self.sp_name))
        delete(ResourceMapping.find("image", payload['id']))


def get_server_for_sp(sp):
    cfg = CONF.__getattr__('sp_%s' % sp)
    endpoints = [
            VolumeCreateEndpoint(cfg.sp_name),
            VolumeDeleteEndpoint(cfg.sp_name),
            SnapshotCreateEndpoint(cfg.sp_name),
            SnapshotDeleteEndpoint(cfg.sp_name),
            ImageCreateEndpoint(cfg.sp_name),
            ImageDeleteEndpoint(cfg.sp_name)
    ]
    transport = oslo_messaging.get_notification_transport(CONF, cfg.messagebus)
    targets = [oslo_messaging.Target(topic='notifications')]
    return oslo_messaging.get_notification_listener(transport, targets, endpoints, executor='eventlet')

if __name__=="__main__":
    LOG.info("Now listening for changes")
    for sp in CONF.proxy.service_providers:
        get_server_for_sp(sp).start()
    while True:
        eventlet.sleep(5) #XXX do something moderately more intelligent than this...
