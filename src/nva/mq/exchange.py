# -*- coding: utf-8 -*-

import kombu
from zope import schema
from zope.interface import Interface, implementer
from zope.configuration import fields
from zope.component.zcml import utility
from zope.configuration.config import ConfigurationContext
from zope.configuration.interfaces import IConfigurationContext
from zope.configuration.interfaces import IGroupingContext


class IExchange(Interface):
    pass


class IExchangeDirective(Interface):
    """Group security declarations about a module"""

    factory = fields.GlobalObject(
        title=u"Exchange class",
        required=False,
        default=kombu.Exchange)

    name = schema.ASCIILine(
        title=u"Name of the AMQP exchange",
        required=True,
        )

    type = schema.Choice(
        title=u"Type of distribution",
        required=True,
        default=u'direct',
        values=('direct', 'topic', 'fanout', 'headers'),
        )


@implementer(IConfigurationContext, IGroupingContext)
class ExchangeDecorator(ConfigurationContext):
    """Helper mix-in class for building grouping directives

    See the discussion (and test) in GroupingStackItem.
    """

    def __init__(self, context, factory=kombu.Exchange, name='', type='direct'):
        self.context = context
        self.exchange = factory(name, type=type)
        self.name = name

    def __getattr__(self, name,
                    getattr=getattr, setattr=setattr):
        v = getattr(self.context, name)
        # cache result in self
        setattr(self, name, v)
        return v

    def before(self):
        pass

    def after(self):
        utility(self.context, IExchange, self.exchange, name=self.name)
