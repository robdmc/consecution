#! /usr/bin/env python

from collections import namedtuple
from multiprocessing import Process, Pipe
from signal import signal, SIGTERM, SIGINT

Connection = namedtuple('Connection', ['parent', 'child'])


#class MonitoredCall(object):
#    def __init__(self):
#        self.connection = Connection(*Pipe())
#
#    def __call__(self):
#        try:
#            print 'spawned process called'
#            1/0
#
#            self.connection.child.send('ok')
#
#        except:
#            self.connection.child.send('fail')
#
#
#def main():
#    mc = MonitoredCall()
#    p = Process(target=mc)
#    p.start()
#    print 'returned', mc.connection.parent.recv()
#    p.join()


#def with_monitoring(func):
#    #connection = Connection(*Pipe())
#    connection_factory = lambda: Connection(*Pipe())
#    def out_func(*args, **kwargs):
#        connection = connection_factory()
#        try:
#            func(*args, **kwargs)
#            connection.child.send('ok')
#        except:
#            connection.child.send('fail')
#
#    out_func.connection = connection
#    return out_func
#
#
#@with_monitoring
#def process():
#    print 'spawned process called'
#    1/0


#p = Process(target=process)
#p.start()
#print 'returned', process.connection.parent.recv()
#p.join()



class Node(object):
    def __init__(self, func, name):
        self.connection = Connection(*Pipe())
        self.func = func
        self.name = name

    def __call__(self, *args, **kwargs):
        try:
            self.func(*args, **kwargs)
            self.connection.child.send(('ok', self.name))
        except:
            self.connection.child.send(('fail', self.name))


def process(name):
    if name == 'node_a':
        raise StandardError()
    print 'spawned process called for name {}'.format(name)

node_a = Node(process, 'node_a')
node_b = Node(process, 'node_b')

proc_list = []
node_list = [node_a, node_b]
for node in node_list:
    proc = Process(target=node, args=(node.name,))
    proc_list.append(proc)
    proc.start()

for proc, node in zip(proc_list, node_list):
    print 'returned', node.connection.parent.recv()
    proc.join()


#import zmq
#import time
#from threading import Thread
#import sys
#from uuid import uuid4
##from zmq.eventloop import ioloop, zmqstream
##ioloop.install()
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
