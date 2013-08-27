# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


from .interfaces import IMQSender
from zope.interface import implements
from kombu import Connection
from kombu.common import maybe_declare
from kombu.pools import producers


class MQSender(object):
    implements(IMQSender)

    def __init__(self, DSN):
        self.connection = Connection(DSN)

    def send(self, routing_key, exchange, payload):
        with producers[self.connection].acquire(block=True) as producer:
            maybe_declare(exchange, producer.channel)
            producer.publish(
                payload,
                exchange=exchange,
                routing_key=routing_key)

