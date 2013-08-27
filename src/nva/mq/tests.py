import unittest
from nva.mq.manager import MQDataManager, Message
from nva.mq.components import MQSender


class FileSafeDataManagerTests(unittest.TestCase):

    def setUp(self):
        self.dm = MQDataManager()
        self.message = Message()

    def testEmptyDM(self):
        self.assertEqual(len(self.dm.messages), 0)

    def testCreateMessage(self):
        self.dm.createMessage(self.message)
        self.assertEqual(len(self.dm.messages), 1)
        self.assertEqual(list(self.dm.messages.keys()), [self.message.__hash__()])

    def testFailIfCreateMessageTwice(self):
        self.dm.createMessage(self.message)
        self.assertRaises(ValueError, self.dm.createMessage, self.message)


class MQSenderTests(unittest.TestCase):

    def setUp(self):
        from kombu import Exchange
        self.sender = MQSender('amqp://guest:guest@localhost:5672//')
        self.exchange = Exchange('tasks', type='direct')

    def testSimpleSend(self):
        self.sender.send('hipri', self.exchange, "BLA")
