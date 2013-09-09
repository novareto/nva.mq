# -*- coding: utf-8 -*-

from .interfaces import IReader, IPoller
from cromlech.configuration.utils import load_zcml
from cromlech.zodb.controlled import Connection as ZODBConnection
from cromlech.zodb.utils import init_db
from kombu import Consumer, Connection as AMQPConnection
from kombu.utils import nested
from nva.mq import log
from nva.mq.interfaces import IListener, IProcessor
from nva.mq.queue import IReceptionQueue
from zope.component import getUtility, getUtilitiesFor
from zope.interface import implementer, provider
import socket
import transaction


def processor(name, **data):
    handler = getUtility(IProcessor, name=name)

    def process(body, message):
        log.debug('Receiving Message in Exchange %s, with RoutingKey %s' % (
            message.delivery_info['exchange'],
            message.delivery_info['routing_key']))
        errors = handler(body, message, **data)
        if errors is None:
            message.ack()
    return process


@implementer(IReader)
class BaseReader(object):

    def __init__(self, url):
        self.url = url

    def poll(self, queues, timeout=None, **data):
        log.debug('Starting Poller for %s, %s' % (queues.keys(), data))
        with AMQPConnection(self.url) as conn:
            consumers = [Consumer(conn.channel(), queues=[queue],
                                  callbacks=[processor(name, **data)])
                         for name, queue in queues.items()]
            with nested(*consumers):
                while True:
                    try:
                        conn.drain_events(timeout=timeout)
                    except socket.timeout:
                        break


def zcml_ignited(func):
    def zcml_decorated(*args, **kwargs):
        filename = kwargs.pop('zcml_file', None)
        if filename is not None:
            load_zcml(filename)
        print kwargs
        return func(*args, **kwargs)
    return zcml_decorated
        

def get_reader(url, name=u''):
    listener = getUtility(IListener, name=name)
    return listener(url)


@zcml_ignited
@provider(IPoller)
def poller(url, timeout):
    queues = dict(getUtilitiesFor(IReceptionQueue))
    receiver = get_reader(url)
    receiver.poll(queues, timeout=timeout)


@zcml_ignited
@provider(IPoller)
def zodb_aware_poller(url, timeout, zodb_conf=None, **data):
    queues = dict(getUtilitiesFor(IReceptionQueue))
    receiver = get_reader(url)
    tm = transaction.TransactionManager()
    db = init_db(open(zodb_conf, 'r').read())
    with ZODBConnection(db, transaction_manager=tm) as zodb:
        with tm:
            data['db_root'] = zodb
            receiver.poll(queues, timeout=timeout, **data)

