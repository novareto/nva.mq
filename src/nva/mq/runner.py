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
from grokcore.component import global_utility
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
        processor = getUtility(IProcessor, name=body['processor'])
        processor(body)
        message.ack()


class BaseReader(object):

    worker = Worker

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
                    Worker(conn, queues, tm, site).run()


global_utility(BaseReader, provides=IReceiver)


def init(name, conf_file):
    with open(conf_file, 'r') as fs:
        config = fs.read()
    db = init_db(config)
    return db


def main(zodb_conf, app, url, zcml=None):

    if zcml:
        load_zcml(zcml)

    db = init(app, zodb_conf)
    receiver = getUtility(IReceiver)
    receiver.start(url, db, app, ['info'])
