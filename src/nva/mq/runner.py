# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import transaction
from grokcore.component import global_utility
from nva.mq.interfaces import ISender, IListener
from nva.mq.manager import Message, MQTransaction
from nva.mq.queue import IEmissionQueue
from zope.component import getUtility, getGlobalSiteManager, getUtilitiesFor
from nva.mq import log, reader


#test purposes
global_utility(reader.BaseReader, IListener, direct=True)


class Sender(object):

    def __init__(self, url, queues):
        self.url = url
        self.queues = queues

    def send(self, message):
        with transaction.manager as tm:
            log.debug('Sending Message for routing_key %s' % (message.type))
            with MQTransaction(self.url, self.queues, tm) as message_manager:
                message_manager.createMessage(message)


def test_processor(queue, name):
    def info_processor(body, message, **data):
        print body, message, data
    return info_processor


@reader.zcml_ignited
def sender(url):
    """Used for test purposes.
    """
    gsm = getGlobalSiteManager()

    queues = dict(getUtilitiesFor(IEmissionQueue))
    sender = Sender(url, queues.values)
    gsm.registerUtility(sender, ISender, name="info")

    test_sender = getUtility(ISender, name="info")
    message = Message('info', **{'message': 'ping'})
    test_sender.send(message)


def poller(url, timeout=1, zcml_file=None, zodb_file=None):
    if zodb_file:
        reader.zodb_aware_poller(
            url, timeout, zcml_file=zcml_file, zodb_file=zodb_file)
    else:
        reader.poller(url, timeout, zcml_file=zcml_file)
