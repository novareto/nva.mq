import unittest
from nva.mq.manager import MQDataManager, Message
from nva.mq.components import MQSender
from kombu import Exchange, Queue, Consumer, Connection
from kombu.mixins import ConsumerMixin


URL = "memory://localhost:8888//"
EXCHANGE = Exchange("messages", type="direct")
QUEUES = dict(
    alert=Queue("alert", EXCHANGE, routing_key="alert"),
    info=Queue("info", EXCHANGE, routing_key="info"),
)


RESULTS = []


class Reader(ConsumerMixin):
    '''Reads one message then quits.
    If no message is available : wait.
    '''

    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=QUEUES.values(), callbacks=[self.read])]

    def read(self, body, message):
        RESULTS.append(message)
        message.ack()
        self.should_stop = True


def rabbitmq_receive(url):
    with Connection(url) as conn:
        Reader(conn).run()


class FileSafeDataManagerTests(unittest.TestCase):

    def setUp(self):
        self.dm = MQDataManager(
            url=URL,
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
        self.assertEqual(len(RESULTS), 0)
        rabbitmq_receive(URL)
        self.assertEqual(len(RESULTS), 1)
        message = RESULTS[0]
        self.assertEqual(message.body, '{"message": "BLA"}')
