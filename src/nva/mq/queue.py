# -*- coding: utf-8 -*-

import kombu
from zope import schema
from zope.interface import Interface
from zope.component.zcml import utility


class IQueue(Interface):
    pass


class IMQQueueDirective(Interface):
    """Make statements about a class"""

    name = schema.ASCIILine(
        title=u"Name of the AMQP queue",
        required=True,
        )

    routing_key = schema.ASCIILine(
        title=u"Routing key of the AMQP queue",
        required=False,
        default="default",
        )


def mq_queue(context, name, routing_key=u"default"):
    queue = kombu.Queue(name, context.exchange, routing_key)
    utility(context, IQueue, queue, name=name)
