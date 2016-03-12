#! /usr/bin/env python

from collections import namedtuple
from multiprocessing import Process
from uuid import uuid4
import sys
import time
import zmq

#Connection = namedtuple('Connection', ['uri', 'socket'])

class ConnectionBase(object):
    def __init__(self, uri, socket):
        self.uri = uri
        self.socket = socket
        self.link_uri()

class PullConnection(ConnectionBase):
    def __init__(self, *args, **kwargs):
        super(PullConnection, self).__init__(*args, **kwargs)
        self.socket.connect(self.socket.uri)
    def handle(self):
        try:
            item = socket_pull.recv_pyobj()
        except:
            self.handle_error()


    def link_uri(self):
        if self.socket.socket_type in [zmq.PUSH, zmq.REP]:
            self.socket.bind(self.socket.uri)

        elif self.socket.socket_type in [zmq.PULL, zmq.REQ]:
            self.socket.connect(self.socket.uri)

    def handle(self):
                item = socket_pull.recv_pyobj()



class Node(object):
    def __init__(self, name):
        self.context = zmq.Context()
        self.name = name

        # pull data from upstream
        self.pull_connection = Connection(
            '',
            None,
        )

        # pushes data to downstream
        self.push_connection = Connection(
            'ipc:///tmp/node_data_{}.sock'.format(uuid4()),
            self.context.socket(zmq.PUSH),
        )
        self.link_uri(self.push_connection)

        # accepts control signals to alter behavior
        self.control_connection = Connection(
            'ipc:///tmp/node_control_{}.sock'.format(uuid4())
            self.context.socket(zmq.REP),
        )
        self.link_uri(self.control_connection)

        # send out status information such as "I'm awake," or "I'm dying"
        self.status_connection = Connection(
            'ipc:///tmp/node_status_{}.sock'.format(uuid4())
            self.context.socket(zmq.REQ),
        )
        self.link_uri(self.status_connection)

    def link_uri(self, connection):

        if connection.socket.socket_type == zmq.PUSH:
            connection.socket.bind(connection.socket.uri)

        elif connection.socket.socket_type == zmq.PULL:
            connection.socket.connect(connection.socket.uri)

        elif connection.socket.socket_type == zmq.REQ:
            connection.socket.connect(connection.socket.uri)

        elif connection.socket.socket_type == zmq.REP:
            connection.socket.bind(connection.socket.uri)

    def handle_error(self, err):
        pass

    def handle_pull(self):
        try:
            pass
        except:
            self.handle_error(err)

    def handle_control(self):
        try:
            pass
        except:
            self.handle_error(err)

    def run(self):
        #  register monitored connections with poller
        conns = [self.pull_connection, self.control_connection]
        monitored_connections = [c for c in conns if c.socket is not None]
        poller = zmq.Poller()
        for conn in monitored_connections:
            poller.register(conn.socket, zmq.POLLIN)

        stay_alive = True
        while stay_alive:
            socks = dict(poller.poll())
            if self.pull_connection.socket in socks and socks[self.pull_connection.socket] == zmq.POLLIN:
                self.handle_pull(self.pull_connection)
            elif self.control_connection.socket in socks and socks[self.control_connection.socket] == zmq.POLLIN:
                self.handle_pull(self.pull_connection)





                item = socket_pull.recv_pyobj()



                message = socket_pull.recv()
                print "Recieved control command: %s" % message
                if message == "Exit": 
                    print "Recieved exit command, client will stop recieving messages"
                    should_continue = False

            if socket_sub in socks and socks[socket_sub] == zmq.POLLIN:
                string = socket_sub.recv()
                topic, messagedata = string.split()
                print "Processing ... ", topic, messagedata


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
