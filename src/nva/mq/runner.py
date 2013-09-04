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
from nva.mq.queue import IQueue
from zope.component import getUtility, getGlobalSiteManager

# To use to find the root
# should be used in a processor, then, probably not here
# from zope.app.publication.zopepublication import ZopePublication


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

    listener = getUtility(IListener)
    receiver = listener(url)

    tm = transaction.TransactionManager()
    if zodb_conf:
        db = init_db(zodb_conf)
        with ZODBConnection(db, transaction_manager=tm):
            with tm:
                receiver.poll(['info'], timeout=2, **{'db_root': db})
    else:
         receiver.poll(['info'], timeout=2)   

         
class Sender(object):

    def __init__(self, url, qids):
        self.url = url
        self.qids = qids

    def send(self, message):
        queues = [getUtility(IQueue, name=qid) for qid in self.qids]
        with transaction.manager as tm:
            with MQTransaction(self.url, queues, tm) as message_manager:
                message_manager.createMessage(message)
                
            
def sender(url=None, zcml_file=None):
    """Used for test purposes.
    """
    if zcml_file:
        load_zcml(zcml_file)

    gsm = getGlobalSiteManager()
    sender = Sender(url, ['info'])
    gsm.registerUtility(sender, ISender, name="info")

    test_sender = getUtility(ISender, name="info")
    message = Message('info', **{'message': 'ping'})
    test_sender.send(message)
