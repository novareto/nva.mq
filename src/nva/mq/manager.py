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
    def publish(payload, connection, queue):
        with producers[connection].acquire(block=True) as producer:
            maybe_declare(queue, producer.channel)
            producer.publish(
                payload, serializer="pickle", routing_key=self.type)

    

@implementer(IDataManager)
class MQDataManager(object):

    def __init__(self, url, queue):
        self.url = url
        self.queue = queue
        self.messages = {}

    def createMessage(self, message):
        if message.__hash__() in self.messages.keys():
            raise ValueError('%s MessageHash already there' %message.__hash__())
        self.messages[message.id] = message

    def commit(self, transaction):
        with Connection(self.url) as conn:
            for message in self.messages.values():
                payload = message.dump()
                message.publish(payload, conn, self.queue)

    def abort(self, transaction):
        self.messages = {}

    def tpc_begin(self, transaction):
        pass

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        self.state = CLOSED

    def tpc_abort(self, transaction):
        pass

    def sortKey(self):
        return "~nva.mq"


class MQTransaction(object):

    def __init__(self, url, queue, transaction_manager=None):
        self.url = url
        self.queue = queue
        if transaction_manager is None:
            transaction_manager = transaction.manager
        self.transaction_manager = transaction_manager

    def __enter__(self):
        dm = MQDataManager(self.url, self.queue)
        self.transaction_manager.join(dm)
        return dm
  
    def __exit__(self, type, value, traceback):
        pass
