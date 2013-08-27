# -*- coding: utf-8 -*-

import optparse
import transaction
from nva.mq.manager import Message, MQTransaction
from kombu import Exchange, Queue


task_exchange = Exchange("tasks", type="direct")
task_queues = [
    Queue("alerts", task_exchange, routing_key="alert"),
    Queue("infos", task_exchange, routing_key="info"),
    ]



def rabbitmq_sender(url):
    message = Message(u"Hey, i'm here", type='info')
    with transaction.manager as tm:
        with MQTransaction(url, task_exchange, tm) as message_manager:
            message_manager.createMessage(message)


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option(
        '--host', dest="host", default='localhost',
        help=u'Host of the AMQP server.')
    parser.add_option(
        '--user', dest="user", default='guest',
        help=u'Username for the AMQP server authentication.')
    parser.add_option(
        '--password', dest="password", default='guest',
        help=u'Password for the AMQP server authentication.')
    parser.add_option(
        '--vhost', dest="vhost", default='nva',
        help=u'Resource for the AMQP server authentication.')
    try:
        options, _ = parser.parse_args()
    except ValueError:
        print >>sys.stderr, parser.format_help()
        sys.exit(1)

    url = "amqp://%s:%s@%s/%s/" % (
        options.user, options.password, options.host, options.vhost)
    rabbitmq_sender(url)
