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


class IReader(Interface):
    """An IReader is a receiving policy object in charge of starting 
    the polling of the queues and propagting the arguments through the
    whole process.
    """

    def __init__(url):
        """Initializes the reader for the given URL.
        """
    
    def poll(queues, timeout, **data):
        """Starts the polling for the given queues.
        If `timeout` is not None and set to an integer value, the polling
        will be interrupted after `timeout` seconds of inactivity.
        `data` is a dict-like structure propagated through to the processor.
        """


class IPoller(Interface):

    def __call__(url, timeout, *args, **data):
        """Starts the polling process.
        If timeout is set, the process is interrupt after `timeout` seconds
        of inactivity.
        """
