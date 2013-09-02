# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


from zope.component import Interface

class ISender(Interface):

    def send(message):
        pass
        

class IReceiver(Interface):

    def start(url, db, appname, queues):
        pass


class IProcessor(Interface):

    def __call__(data):
        pass
