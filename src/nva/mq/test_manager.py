# -*- coding: utf-8 -*-

import socket
import pytest
import unittest
from nva.mq.manager import MQDataManager, Message
from kombu import Connection, Consumer, Exchange, Queue
from zope.configuration.xmlconfig import xmlconfig
from cStringIO import StringIO

ZCML = """
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:meta="http://namespaces.zope.org/meta"
    xmlns:amqp="http://namespaces.novareto.de/amqp">

  <include package="nva.mq" file="meta.zcml" />

  <amqp:exchange
      name="messages"
      type="direct">

     <amqp:queue
         name="info"
         routing_key="info" />

  </amqp:exchange>

</configure>
"""


TEST_URL = "memory://localhost:8888//"

EXCHANGE = Exchange("messages", type="direct")
QUEUES = dict(
    alert=Queue("alert", EXCHANGE, routing_key="alert"),
    info=Queue("info", EXCHANGE, routing_key="info"),
)


def receiver(url, callback):
    def receive():
        with Connection(url) as conn:
            with Consumer(conn, QUEUES.values(), callbacks=[callback]):
                conn.drain_events(timeout=0.5)
    return receive


class FileSafeDataManagerTests(unittest.TestCase):

    def read(self, body, message):
        self.received.append(body)
        message.ack()

    def setUp(self):
        self.received = []
        self.dm = MQDataManager(url=TEST_URL, queues=QUEUES)
        self.message = Message('BLA', 'info')
        self.receive = receiver(TEST_URL, self.read)

    def testEmptyDM(self):
        self.assertEqual(len(self.dm.messages), 0)

    def testCreateMessage(self):
        self.dm.createMessage(self.message)
        self.assertEqual(len(self.dm.messages), 1)
        self.assertEqual(list(self.dm.messages.keys()), [self.message.__hash__()])

    def testFailIfCreateMessageTwice(self):
        self.dm.createMessage(self.message)
        self.assertRaises(ValueError, self.dm.createMessage, self.message)

    def testAbortMessages(self):
        self.dm.createMessage(self.message)
        self.assertEqual(len(self.dm.messages), 1)
        self.dm.abort(None)
        self.assertEqual(len(self.dm.messages), 0)

    def testSendingMessage(self):
        import transaction
        xmlconfig(StringIO(ZCML))
        tr = transaction.begin()
        tr.join(self.dm)
        self.dm.createMessage(self.message)
        transaction.commit()
        self.receive()
        assert self.received == [{u'message': u'BLA'}]
        self.received = []

    def test_abortion(self):
        import transaction
        tr = transaction.begin()
        tr.join(self.dm)
        self.dm.createMessage(self.message)
        transaction.abort()
        with pytest.raises(socket.timeout):
            self.receive()
        assert self.received == []
