# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


import logging
import threading
import transaction
from kombu import Connection
from kombu.common import maybe_declare
from kombu.pools import producers
from zope.interface import implementer
from transaction.interfaces import IDataManager

log = logging.getLogger("nva.mq")


class Message(object):

    def __init__(self, message, type):
        self.message = message
        self.type = type
    
    @property
    def id(self):
        return self.__hash__()

    def dump(self):
        return {'message': self.message}
        
    @staticmethod
    def publish(payload, connection, queue, routing_key):
        exchange = queue.exchange
        with connection.Producer(serializer='json') as producer:
            producer.publish(
                payload, exchange=exchange, routing_key=routing_key, 
                declare=[queue])

    

@implementer(IDataManager)
class MQDataManager(object):

    def __init__(self, url, queues):
        self.url = url
        self.queues = queues
        self.messages = {}

    def createMessage(self, message):
        if message.__hash__() in self.messages.keys():
            raise ValueError('%s MessageHash already there' %message.__hash__())
        self.messages[message.id] = message

    def commit(self, transaction):
        with Connection(self.url) as conn:
            for message in self.messages.values():
                payload = message.dump()
                queue = self.queues.get(message.type)
                message.publish(payload, conn, queue, message.type)

    def abort(self, transaction):
        self.messages = {}

    def tpc_begin(self, transaction):
        pass

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        pass

    def tpc_abort(self, transaction):
        pass

    def sortKey(self):
        return "~nva.mq"


class MQTransaction(object):

    def __init__(self, url, queues, transaction_manager=None):
        self.url = url
        self.queues = queues
        if transaction_manager is None:
            transaction_manager = transaction.manager
        self.transaction_manager = transaction_manager

    def __enter__(self):
        dm = MQDataManager(self.url, self.queues)
        self.transaction_manager.join(dm)
        return dm
  
    def __exit__(self, type, value, traceback):
        pass
