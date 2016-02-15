#! /usr/bin/env python

from collections import namedtuple
from multiprocessing import Process
from uuid import uuid4
import sys
import time
import zmq

Connection = namedtuple('Connection', ['uri', 'socket'])


class Node(object):
    def __init__(self, name):
        self.context = zmq.Context()
        self.name = name

        # pushes data to downstream
        self.push_connection = Connection(
            'ipc:///tmp/node_data_{}.sock'.format(uuid4()),
            self.context.socket(zmq.PUSH)
        )

        # pull data from upstream
        self.pull_connection = Connection(
            '',
            None,
        )

        # accepts control signals to alter behavior
        self.control_connection = Connection(
            'ipc:///tmp/node_control_{}.sock'.format(uuid4())
            self.context.socket(zmq.REP)
        )

        # send out status information such as "I'm awake," or "I'm dying"
        self.status_connection = Connection(
            'ipc:///tmp/node_status_{}.sock'.format(uuid4())
            self.context.socket(zmq.REQ)
        )

    def activate_connection(self, connection):
        def connect(connection):
            connection.socket.connect(connection.socket.uri)
        def bind(connection):
            connection.socket.bind(connection.socket.uri)

        link = {
            zmq.PULL: connect,
            zmq.PUSH: bind,
            zmq.REP: bind,
            zmq.REQ: connect
        }

        link[connection](connection)









    def run(self):
        # initialize monitored connections
        conns = [self.pull_connection, self.control_connection]
        monitored_connections = [c for c in conns if c.socket is not None]

        poller = zmq.Poller()
        for conn in monitored_connections:
            poller.register(conn.socket, zmq.POLLIN)

    def process(self, item):
        pass

#
#SOCKET_URI = 'ipc:///tmp/zmq_sock_{}'.format(uuid4())
#
#def handle_stop(*args, **kwargs):
#    sys.stderr.write('keyboard interrupt detected.  Killing process')
#
#class EndSentinal(object):
#    def __str__(self):
#        return 'end_sentinal'
#    def __repr__(self):
#        return self.__str__()
#
#
#def pusher(connection):
#    try:
#        print 'starting pusher'
#        context = zmq.Context() if context is None else context
#        socket = context.socket(zmq.PUSH)
#        socket.bind(SOCKET_URI)
#        for nn in range(10):
#            msg = 'item {}'.format(nn)
#            socket.send_pyobj(msg)
#            time.sleep(.2)
#        socket.send_pyobj(EndSentinal())
#        connection.send('done')
#    except:
#        connection.send('error')
#
#
#def pull_handler(msg):
#    print 'handling {}'.format(msg)
#    raise StandardError()
#
#def puller(connection):
#    try:
#        context = zmq.Context() if context is None else context
#        socket = context.socket(zmq.PULL)
#        socket.connect(SOCKET_URI)
#
#        poller = zmq.Poller()
#        poller.register(socket, zmq.POLLIN)
#
#        keepon = True
#        while keepon:
#            socks = dict(poller.poll())
#            if socket in socks and socks[socket] == zmq.POLLIN:
#                msg = socket.recv_pyobj()
#
#                if isinstance(msg, EndSentinal):
#                    break
#                else:
#                    pull_handler(msg)
#        connection.send('ok')
#    except:
#        connection.send('error')
#
#
#
#
#
#
##signal(SIGTERM, handle_stop)
##signal(SIGINT, handle_stop)
#
##context = zmq.Context()
##pusher_thread = Thread(target=pusher, args=(context,))
##puller_thread = Thread(target=puller, args=(context,))
#
#push_parent, push_child = Pipe()
#pull_parent, pull_child = Pipe()
#
#pusher_thread = Process(target=pusher, args=(push_child))
#puller_thread = Process(target=puller, args=(pull_child))
#
##pusher_thread.daemon = True
##puller_thread.daemon = True
#
#p_push = pusher_thread.start()
#p_pull = puller_thread.start()
#
#
#
##pusher_thread.join()
##puller_thread.join()
#
#
#
#
#
#
#
#
#
#
#
#
