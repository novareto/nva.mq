
# -*- coding: utf-8 -*-

import optparse
import transaction
from nva.mq.manager import Message, MQTransaction
from kombu.mixins import ConsumerMixin
from kombu import Connection, Consumer, Exchange, Queue


exchange = Exchange("messages", type="direct")
queues = dict(
    alert = Queue("alert", exchange, routing_key="alert"),
    info = Queue("info", exchange, routing_key="info"),
    )


class Reader(ConsumerMixin):
    '''Reads one message then quits.
    If no message is available : wait.
    '''

    def __init__(self, connection):
        self.connection = connection
 
    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=queues.values(), callbacks=[self.read])]
 
    def read(self, body, message):
        print body
        message.ack()
        self.should_stop = True


def rabbitmq_receive(url):
    with Connection(url) as conn:
        Reader(conn).run()


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
        '--vhost', dest="vhost", default='/',
        help=u'Resource for the AMQP server authentication.')
    try:
        options, _ = parser.parse_args()
    except ValueError:
        print >>sys.stderr, parser.format_help()
        sys.exit(1)

    url = "amqp://%s:%s@%s/%s" % (
        options.user, options.password, options.host, options.vhost)
    rabbitmq_receive(url)

