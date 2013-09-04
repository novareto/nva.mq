# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from zope.component import Interface
from zope.component.interfaces import IFactory


class ISender(Interface):

    def send(message):
        pass
        

class IReceiver(Interface):

    def receive(queue_ids, limit=None, timeout=None, **data):
        """Receive the messages on the queues defined by `queue_ids`
        `limit` : number of message to receive before quitting
        `timeout`: timeout before dsconnection
        `data`: dict-like datastructure passed to the task processor.
        """
        

class IProcessor(Interface):

    def __call__(body, message, **data):
        pass



class IListener(IFactory):

    def __call__(url):
        """Returns an instance of an IReicever for the given url.
        """



    
