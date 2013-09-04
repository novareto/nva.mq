# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import os
import argparse
import transaction
import socket
from kombu.utils import nested
from cromlech.configuration.utils import load_zcml
from cromlech.zodb.controlled import Connection as ZODBConnection
from cromlech.zodb.utils import init_db
from grokcore.component import global_utility
from kombu import Consumer, Connection as AMQPConnection
from kombu.common import drain_consumer, itermessages
from nva.mq.interfaces import IListener, IReceiver, IProcessor
from nva.mq.manager import Message, MQTransaction
from nva.mq.queue import IQueue
from zope.app.publication.zopepublication import ZopePublication
from zope.component import getUtility
from zope.interface import Interface
from zope.app.publication.zopepublication import ZopePublication
from cromlech.zodb.controlled import Connection as ZODBConnection
from kombu import Connection as AMQPConnection
from kombu.mixins import ConsumerMixin


def resolve_queues(qids):
    for qid in qids:
        try:
            queue = getUtility(IQueue, name=qid)
            yield qid, queue
        except:
            # handle me
            raise


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

    def poll(self, qids, limit=None, timeout=None, **data):
        print "--Starting the poller for %s, %s--" % (qids, data)
        queues = resolve_queues(qids)
        with AMQPConnection(self.url) as conn:
            consumers = [Consumer(conn.channel(), queues=[queue],
                                  callbacks=[processor(name, **data)])
                for name, queue in queues]
            with nested(*consumers):
                while True:
                    try:
                        conn.drain_events(timeout=timeout)
                    except socket.timeout:
                        break

                    
global_utility(BaseReader, provides=IListener, direct=True)


def info_processor(body, message, **data):
    print body, message, data


global_utility(info_processor, provides=IProcessor, direct=True, name="info")
    

def poller(zodb_conf=None, app="app", url=None, zcml_file=None):

    if zcml_file:
        load_zcml(zcml_file)

    db = init_db(zodb_conf)
    
    listener = getUtility(IListener)
    receiver = listener(url)

    tm = transaction.TransactionManager()
    with ZODBConnection(db, transaction_manager=tm) as zodb:
        with tm:
           receiver.poll(['info'], timeout=2, **{'db_root': db})


def sender(url=None, zcml_file=None):
    """Used for test purposes.
    """
    if zcml_file:
        load_zcml(zcml_file)

    message = Message('info', **{'message': 'ping'})
    queue = getUtility(IQueue, name='info')
    with transaction.manager as tm:
        with MQTransaction(url, [queue], tm) as message_manager:
            message_manager.createMessage(message)
