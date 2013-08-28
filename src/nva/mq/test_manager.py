import unittest
from nva.mq.manager import MQDataManager, Message
from nva.mq.components import MQSender
from kombu import Exchange, Queue


EXCHANGE = Exchange("messages", type="direct")
QUEUES = dict(
    alert=Queue("alert", EXCHANGE, routing_key="alert"),
    info=Queue("info", EXCHANGE, routing_key="info"),
)


class FileSafeDataManagerTests(unittest.TestCase):

    def setUp(self):
        self.dm = MQDataManager(
            url="memory://localhost:8888//",
            queues=QUEUES)
        self.message = Message('BLA', 'info')

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
        tr = transaction.begin()
        tr.join(self.dm)
        self.dm.createMessage(self.message)
        transaction.commit()
