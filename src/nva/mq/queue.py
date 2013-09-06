# -*- coding: utf-8 -*-

import kombu
from zope import schema
from zope.interface import Interface
from zope.component.zcml import utility
from zope.configuration.fields import GlobalObject
from .interfaces import IProcessor


class IQueue(Interface):
    pass


class IReceptionQueue(IQueue):
    pass


class IEmissionQueue(IQueue):
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

    processor = GlobalObject(
        title=u"Queue receiving task processor",
        description=(u"If this field is set to None, the queue will not " +
                     u"be available for reception."),
        required=False,
        default=None,
        )

    allow_emission = schema.Bool(
        title=u"Allow message emissions",
        description=u"The queue can be used to propagate messages.",
        required=False,
        default=True,
        )


def mq_queue(context, name,
             routing_key=u"default", processor=None, allow_emission=True):

    if allow_emission is False and processor is None:
        raise ValueError(u'A queue must be able to either send or receive.')

    queue = kombu.Queue(name, context.exchange, routing_key)

    if processor is not None:
        receiver = processor(queue, name)
        utility(context, IProcessor, receiver, name=name)
        utility(context, IReceptionQueue, queue, name=name)

    if allow_emission is True:
        utility(context, IEmissionQueue, queue, name=name)
