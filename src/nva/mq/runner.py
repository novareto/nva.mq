# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import os
import argparse
import transaction
from cromlech.configuration.utils import load_zcml
from cromlech.zodb.utils import init_db
from nva.mq.interfaces import IReceiver
from nva.mq.queue import IQueue
from zope.component import getUtility
from zope.interface import Interface
from zope.app.publication.zopepublication import ZopePublication
from cromlech.zodb.controlled import Connection as ZODBConnection
from kombu import Connection as AMQPConnection
from kombu.mixins import ConsumerMixin

parser = argparse.ArgumentParser(usage="usage: prog [options]")

parser.add_argument(
    '--zodb_conf', dest="zodb_conf", default=None,
    help=u'ZODB configuration file')

parser.add_argument(
    '--zcml', dest="zcml", default=None,
    help=u'ZCML configuration file')

parser.add_argument(
    '--app', dest="app", default='app',
    help=u'App Name')

parser.add_argument(
    '--url', dest="url", default='amqp://guest:quest@locahost//',
    help=u'URL of the AMQP server')


class Worker(ConsumerMixin):

    def __init__(self, connection, queues, tm, site):
        self.connection = connection
        self.site = site
        self.queues = queues
        self.tm = tm
 
    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.queues, callbacks=[self.process])]
 
    def process(self, body, message):
        print body
        message.ack()


class BaseReader(object):

    worker = Worker
    
    def __init__(self, url, db, appname, queues):
        self.url = url
        self.db = db
        self.appname = appname
        self.queues = [getUtility(IQueue, name=queue) for queue in queues]

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.queues, callbacks=[self.read])]

    def start(self):
        tm = transaction.TransactionManager()
        with ZODBConnection(self.db, transaction_manager=tm) as zodb:
            with tm:
                #root = zodb.root()[ZopePublication.root_name]
                #site = root[self.appname]
                site = None
                with AMQPConnection(self.url) as conn:
                    Worker(conn, self.queues, tm, site).run()
    

def init(name, conf_file):
    with open(conf_file, 'r') as fs:
        config = fs.read()
    db = init_db(config)    
    return db


def main():
    args = parser.parse_args()

    if not args.zodb_conf:
        raise RuntimeError('We need a zope conf')

    if args.zcml:
        load_zcml(args.zcml)

    db = init(args.app, args.zodb_conf)
    receiver = BaseReader(args.url, db, args.app, ['info'])
    receiver.start()
