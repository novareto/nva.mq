# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import transaction
import socket
from cromlech.configuration.utils import load_zcml
from cromlech.zodb.controlled import Connection as ZODBConnection
from cromlech.zodb.utils import init_db
from grokcore.component import global_utility
from kombu import Consumer, Connection as AMQPConnection
from kombu.utils import nested
from nva.mq.interfaces import IListener, ISender, IProcessor
from nva.mq.manager import Message, MQTransaction
from nva.mq.queue import IEmissionQueue, IReceptionQueue
from zope.component import getUtility, getGlobalSiteManager, getUtilitiesFor


def processor(name, **data):
    handler = getUtility(IProcessor, name=name)
    def process(body, message):
        errors = handler(body, message, **data)
        if errors is None:
            message.ack()
    return process


class BaseReader(object):

    def __init__(self, url):
        self.url = url

    def poll(self, queues, limit=None, timeout=None, **data):
        print "--Starting the poller for %s, %s--" % (queues.keys(), data)
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

                    
global_utility(BaseReader, provides=IListener, direct=True)


    

def poller(zodb_conf=None, app="app", url=None, zcml_file=None):

    if zcml_file:
        load_zcml(zcml_file)

    listener = getUtility(IListener)
    receiver = listener(url)

    tm = transaction.TransactionManager()
    queues = dict(getUtilitiesFor(IReceptionQueue))
    if zodb_conf:
        db = init_db(zodb_conf)
        with ZODBConnection(db, transaction_manager=tm):
            with tm:
                receiver.poll(queues, timeout=2, **{'db_root': db})
    else:
         receiver.poll(queues, timeout=2)   


class Sender(object):

    def __init__(self, url, queues):
        self.url = url
        self.queues = queues

    def send(self, message):
        with transaction.manager as tm:
            with MQTransaction(self.url, self.queues, tm) as message_manager:
                message_manager.createMessage(message)
                

def test_processor(queue, name):
    def info_processor(body, message, **data):
        print body, message, data
    return info_processor

        
def sender(url=None, zcml_file=None):
    """Used for test purposes.
    """
    if zcml_file:
        load_zcml(zcml_file)

    gsm = getGlobalSiteManager()

    queues = dict(getUtilitiesFor(IEmissionQueue))
    sender = Sender(url, queues.values)
    gsm.registerUtility(sender, ISender, name="info")

    test_sender = getUtility(ISender, name="info")
    message = Message('info', **{'message': 'ping'})
    test_sender.send(message)
