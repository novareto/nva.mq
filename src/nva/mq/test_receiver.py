import unittest
from zope.component import getUtility
from nva.mq.queue import IQueue
from nva.mq.runner import BaseReader, Worker
from nva.mq.manager import MQDataManager, Message

TEST_URL = "memory://localhost:8888//"


class MQReceiverTests(unittest.TestCase):

    def setUp(self):
        self.receiver = BaseReader()
        queues = [getUtility(IQueue, name=queue) for queue in ['info', 'error']]
        self.dm = MQDataManager(url=TEST_URL, queues=queues)

    def testSendingTwoMessages(self):
        import transaction
        #xmlconfig(StringIO(ZCML))
        tr = transaction.begin()
        tr.join(self.dm)
        self.dm.createMessage(Message('info', data="INFO"))
        self.dm.createMessage(Message('error', data="ERROR"))
        transaction.commit()
        from ZODB import DB
        from ZODB.DemoStorage import DemoStorage
        db = DB(DemoStorage('test_storage'))
        self.receiver.start(TEST_URL, db, 'app', ['info', 'error'])
