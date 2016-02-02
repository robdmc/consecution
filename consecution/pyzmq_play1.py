#! /usr/bin/env python

import zmq
import multiprocessing
import time

PORT = 7777
HWM = 1


def producer():
    context = zmq.Context()
    sock = context.socket(zmq.PUSH)
    #sock.setsockopt(zmq.SNDHWM, 1)
    #sock.sndhwm = 1
    sock.hwm = HWM
    sock.bind("tcp://127.0.0.1:{}".format(PORT))
    print 'producer send rcv, hwm', sock.SNDHWM, sock.RCVHWM
    for nn in range(10000):
        #print 'sending',nn 
        s = 'b'*100000000
        #s = 'b'
        sock.send_json({nn: bytes(s)})

def consumer():
    context = zmq.Context()
    sock = context.socket(zmq.PULL)
    #sock.setsockopt(zmq.RCVHWM, 2)
    sock.hwm = HWM
    #sock.rcvhwm = 2
    sock.connect("tcp://127.0.0.1:{}".format(PORT))
    print 'consumer send rcv, hwm', sock.SNDHWM, sock.RCVHWM
    while True:
        val = sock.recv_json()
        #print 'received', val.keys()


p = multiprocessing.Process(target=producer)
c = multiprocessing.Process(target=consumer)
print 'starting producer'
p.start()
print 'p pid', p.pid
print 'starting consumer'
c.start()
c.join()

