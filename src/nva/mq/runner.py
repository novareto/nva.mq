# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import os
import argparse
import zope.app.wsgi
import zope.app.server.main
import zope.app.appsetup.product
from zope.component import getUtility
from nva.mq.interfaces import IReceiver


parser = argparse.ArgumentParser(usage="usage: prog [options]")
parser.add_argument(
    '--zope_conf', dest="zope_conf", default='localhost',
    help=u'Zope Conf File')
parser.add_argument(
    '--app', dest="app", default='app',
    help=u'App Name')


def init(appname, configfile):
    """Initialise the Zope environment (without network servers) and return a
    specific root-level object.
    """
    options = zope.app.server.main.load_options(['-C', configfile])
    zope.app.appsetup.product.setProductConfigurations(options.product_config)

    db = zope.app.wsgi.config(
        configfile,
        schemafile=os.path.join(
            os.path.dirname(zope.app.server.main.__file__), 'schema.xml'))

    root = db.open().root()
    app = root['Application']
    if appname is not None:
        app = app[appname]
    return db, app


def main():
    args = parser.parse_args()
    zope_conf = os.path.join('parts', 'etc', 'zope.conf')
    if args.zope_conf:
        zope_conf = args.zope_conf
    appname = args.app
    db, app = init(appname, zope_conf)
    receiver = getUtility(IReceiver)
    receiver.start('amqp://guest:guest@localhost//', app)
