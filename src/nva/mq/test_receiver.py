# -*- coding: utf-8 -*-

import unittest
import nva.mq.reader
from kombu import Queue
from cStringIO import StringIO
from nva.mq.runner import Sender, poller
from nva.mq.manager import Message
from nva.mq.test_manager import ZCML
from nva.mq.interfaces import IListener
from zope.component import getUtility
from nva.mq.queue import IReceptionQueue, IEmissionQueue
from zope.component import globalregistry as gr, provideUtility
from zope.configuration.xmlconfig import xmlconfig


TEST_URL = "memory://localhost:8888//"

MESSAGES = []


class TestReceiver(object):

    def __init__(self, queue, name):
        self.queue = queue
        self.name = name

    def __call__(self, body, message, **data):
        MESSAGES.append(message)


class MQReceiverTests(unittest.TestCase):

    def setUp(self):
        gr.globalSiteManager = gr.BaseGlobalComponents('test2')
        xmlconfig(StringIO(ZCML))
        provideUtility(nva.mq.reader.BaseReader, IListener)

    def tearDown(self):
        gr.globalSiteManager = gr.base

    def testUtilities(self):
        info = getUtility(IEmissionQueue, name="info")
        error = getUtility(IEmissionQueue, name="error")
        debug = getUtility(IReceptionQueue, name="debug")
        assert isinstance(info, Queue) is True
        assert isinstance(error, Queue) is True
        assert isinstance(debug, Queue) is True

    def testSendingReceivingMessages(self):
        debug = getUtility(IReceptionQueue, name="debug")
        sender = Sender(TEST_URL, [debug, ])
        sender.send(Message('debug', data="BLA"))
        poller(TEST_URL)

