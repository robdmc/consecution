#! /usr/bin/env python

import zmq
import time
import sys
import random
from  multiprocessing import Process

from zmq.eventloop import ioloop, zmqstream
ioloop.install()


def server_push(port="5556"):
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:%s" % port)
    print "Running server on port: ", port
    # serves only 5 request and dies
    for reqnum in range(10):
        if reqnum < 6:
            socket.send("Continue")
        else:
            socket.send("Exit")
            break
        time.sleep (1) 


def server_pub(port="5558"):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    publisher_id = random.randrange(0,9999)
    print "Running server on port: ", port
    # serves only 5 request and dies
    for reqnum in range(10):
        # Wait for next request from client
        topic = random.randrange(8,10)
        messagedata = "server#%s" % publisher_id
        print "%s %s" % (topic, messagedata)
        socket.send("%d %s" % (topic, messagedata))
        time.sleep(1)


def getcommand(msg):
    print "Received control command: %s" % msg
    if msg[0] == "Exit":
        print "Received exit command, client will stop receiving messages"
        should_continue = False
        ioloop.IOLoop.instance().stop()

def process_message(msg):
    print "Processing ... %s" % msg


def client(port_push, port_sub):
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    stream_pull = zmqstream.ZMQStream(socket_pull)
    stream_pull.on_recv(getcommand)
    print "Connected to server with port %s" % port_push

    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect ("tcp://localhost:%s" % port_sub)
    socket_sub.setsockopt(zmq.SUBSCRIBE, "9")
    stream_sub = zmqstream.ZMQStream(socket_sub)
    stream_sub.on_recv(process_message)
    print "Connected to publisher with port %s" % port_sub
    ioloop.IOLoop.instance().start()
    print "Worker has stopped processing messages."


if __name__ == "__main__":
    # Now we can run a few servers 
    server_push_port = "5556"
    server_pub_port = "5558"
    Process(target=client, args=(server_push_port,server_pub_port,)).start()
    Process(target=server_push, args=(server_push_port,)).start()
    Process(target=server_pub, args=(server_pub_port,)).start()


