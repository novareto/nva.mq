import unittest
import transaction
from zope.component import getUtility
from nva.mq.queue import IQueue
from nva.mq.runner import BaseReader, Worker
from nva.mq.manager import MQDataManager, Message
from zope.configuration.xmlconfig import xmlconfig
from cStringIO import StringIO
from zope.component import globalregistry as gr
from ZODB import DB
from ZODB.DemoStorage import DemoStorage

TEST_URL = "memory://localhost:8888//"

from nva.mq.test_manager import ZCML
from cromlech.zodb.controlled import Connection as ZODBConnection
from kombu import Connection as AMQPConnection
from kombu.common import drain_consumer


RECEIVED = []


class TestWorker(Worker):

    def process(self, body, message):
        super(TestWorker, self).process(body, message)
        RECEIVED.append(message)


class TestBaseReader(BaseReader):

    def start(self, url, db, appname, queues):
        print "--Starting %s--" % self
        tm = transaction.TransactionManager()
        queues = [getUtility(IQueue, name=queue) for queue in queues]
        with ZODBConnection(db, transaction_manager=tm) as zodb:
            with tm:
                #root = zodb.root()[ZopePublication.root_name]
                #site = root[appname]
                site = None
                with AMQPConnection(url) as conn:
                    consumer = TestWorker(conn, queues, tm, site)
                    drain_consumer(consumer, limit=1, timeout=1, callbacks=[consumer.process])



class MQReceiverTests(unittest.TestCase):

    def setUp(self):
        gr.globalSiteManager = gr.BaseGlobalComponents('test2')
        xmlconfig(StringIO(ZCML))
        self.receiver = TestBaseReader()
        queues = [getUtility(IQueue, name=queue) for queue in ['info', 'error']]
        self.dm = MQDataManager(url=TEST_URL, queues=queues)
        self.db = DB(DemoStorage('test_storage'))

    def tearDown(self):
        gr.globalSiteManager = gr.base

    def testSendingTwoMessages(self):
        with transaction.manager as tr:
            tr.join(self.dm)
            self.dm.createMessage(Message('info', data={'message': "INFO"}))
            self.dm.createMessage(Message('error', data={'message': "ERROR"}))
        self.receiver.start(TEST_URL, self.db, 'app', ['info', 'error'])
        assert len(RECEIVED) == 2
