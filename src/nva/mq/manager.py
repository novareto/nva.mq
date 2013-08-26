# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


import logging
import threading
import transaction

from zope.interface import implementer
from transaction.interfaces import IDataManager


log = logging.getLogger("repoze.filesafe")

_local = threading.local()


def _remove_manager(*a):
    try:
        del _local.manager
    except AttributeError:
        pass


def _get_manager():
    manager = getattr(_local, 'manager', None)
    if manager is not None:
        return manager

    manager = _local.manager = MQDataManager()
    tx = transaction.get()
    tx.join(manager)
    tx.addAfterCommitHook(_remove_manager)
    return manager


class Message(object):

    @property
    def id(self):
        return self.__hash__()


@implementer(IDataManager)
class MQDataManager(object):

    def __init__(self):
        self.messages = {}

    def createMessage(self, message):
        if message.__hash__() in self.messages.keys():
            raise ValueError('%s MessageHash already there' %message.__hash__())
        self.messages[message.id] = message
