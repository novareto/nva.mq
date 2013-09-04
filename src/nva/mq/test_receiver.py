# -*- coding: utf-8 -*-

import unittest
from zope.component import globalregistry as gr


TEST_URL = "memory://localhost:8888//"


class MQReceiverTests(unittest.TestCase):

    def setUp(self):
        gr.globalSiteManager = gr.BaseGlobalComponents('test2')

    def tearDown(self):
        gr.globalSiteManager = gr.base

    def testSendingTwoMessages(self):
        pass
