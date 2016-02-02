#! /usr/bin/env python

import asyncio
import zmq
import zmq.asyncio
import time

SOCKET_FILE_PATH = '/tmp/consecutor'
NAME_SERVER_PORT = 9876


LOOP = zmq.asyncio.ZMQEventLoop()
asyncio.set_event_loop(LOOP)

class IPCNameServer:
    def __init__(self):
        self.socket_file_path = SOCKET_FILE_PATH
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind('tcp://*:{}'.format(NAME_SERVER_PORT))

    async def process(self):
        while True:
            msg = await self.socket.recv()
            print( msg)


class IPCClient:
    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.socket_file_path = SOCKET_FILE_PATH
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect('tcp://localhost:{}'.format(NAME_SERVER_PORT))

    async def send(self):
        while True:
            await self.socket.send(b'hello')




ipc_srv = IPCNameServer()
ipc_cli = IPCClient()

task = asyncio.gather(ipc_srv.process(), ipc_cli.send())

LOOP.run_until_complete(task)



#class Node(object):
#    def __init__(self, name, context=None, queue_size=None):
#        self.name = name
#        self.context = context if context else zmq.Context()
#        self.upstream_socket = self.context.socket(zmq.PULL)
#        self.downstream_socket = self.context.socket(zmq.PUSH)
#        self.consecutor_socket = self.context.socket(zmq.REQ)
#        if queue_size is not None:
#            self.upstream_socket.hwm = queue_size
#            self.downstream_socket = queue_size
#
#
#class Consecutor(object):
#    def __init__(self, name):
#        self.name = name
#
#
#
#
#
#PORT = 7777
#HWM = 1
#
#
#def producer():
#    context = zmq.Context()
#    sock = context.socket(zmq.PUSH)
#    #sock.setsockopt(zmq.SNDHWM, 1)
#    #sock.sndhwm = 1
#    sock.hwm = HWM
#    sock.bind("tcp://127.0.0.1:{}".format(PORT))
#    print 'producer send rcv, hwm', sock.SNDHWM, sock.RCVHWM
#    for nn in range(10000):
#        #print 'sending',nn 
#        s = 'b'*100000000
#        #s = 'b'
#        sock.send_json({nn: bytes(s)})
#
#def consumer():
#    context = zmq.Context()
#    sock = context.socket(zmq.PULL)
#    #sock.setsockopt(zmq.RCVHWM, 2)
#    sock.hwm = HWM
#    #sock.rcvhwm = 2
#    sock.connect("tcp://127.0.0.1:{}".format(PORT))
#    print 'consumer send rcv, hwm', sock.SNDHWM, sock.RCVHWM
#    while True:
#        val = sock.recv_json()
#        #print 'received', val.keys()
#
#
#p = multiprocessing.Process(target=producer)
#c = multiprocessing.Process(target=consumer)
#print 'starting producer'
#p.start()
#print 'p pid', p.pid
#print 'starting consumer'
#c.start()
#c.join()
#
