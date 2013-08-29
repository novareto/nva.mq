# -*- coding: utf-8 -*-

import optparse
import transaction
from nva.mq.queue import IQueue
from nva.mq.manager import Message, MQTransaction
from cromlech.configuration.utils import load_zcml
from zope.component import getUtility


def rabbitmq_sender(url):
    message = Message(u"Hey, i'm here", type='info')
    queue = getUtility(IQueue, name='info')
    with transaction.manager as tm:
        with MQTransaction(url, [queue], tm) as message_manager:
            message_manager.createMessage(message)


if __name__ == "__main__":
    
    parser = optparse.OptionParser(usage="usage: %prog [options]")

    parser.add_option(
        '--url', dest="url", default='amqp://guest:guest@localhost//',
        help=u'Host of the AMQP server.')
    
    parser.add_option(
        '--zcml', dest="zcml", default=None,
        help=u'ZCML file to read.')

    try:
        options, _ = parser.parse_args()
    except ValueError:
        print >>sys.stderr, parser.format_help()
        sys.exit(1)

    if options.zcml is not None:
        load_zcml(options.zcml)

    rabbitmq_sender(options.url)
