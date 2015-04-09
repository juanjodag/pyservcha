#!/usr/bin/env python
'''

server usage:

python server.py [ip address] [port]

'''

import socket
import time
import sys
import json
import conf

owner = conf.owner
name = conf.name
UDP_IP = conf.ip
UDP_PORT = conf.port

print("Welcome to %s server console for your chat room\n please report any bugs to support@sorch.info" % name)
time.sleep(1)
print("Active and listening for connections on port %s and ip %s" % (UDP_PORT, UDP_IP))
# create a datagram socket
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

# bind the socket to a port, to allow people to send info to it
sock.bind((UDP_IP, UDP_PORT))

#  keep a list of "connected" clients, even though we're not really
#  accepting connections per se. The purpose of this is to allow us
#  to replay chat messages to other people and
#  to see who's in the chatroom, etc
clients = []

#  this function sends a message to everyone who is "connected"
def broadcast(data, user):
    global clients
    for client in clients:
        if client[0] != user:
            sock.sendto(data, client[1])


def send_ack(client):
    print 'sending ack'
    sock.sendto(json.dumps({"detail": "Ok"}), client[1])
#  main loop for the server
#  in this loop we try to receive data on the socket
#  and then we relay the message to other clients
while True:
    data = None
    message = None
    try:
        # try to get a message on the socket
        data, addr = sock.recvfrom(1024, socket.MSG_DONTWAIT)  # buffer size is 1024 bytes

        #  if there's a message, then parse it and add the client to the list
        #  if they're a new client
        message = json.loads(data)
        client = (message['sender'], addr)
        if client not in clients:
            clients.append(client)
    #  if no message was available, just wait a while
    except socket.error:
        # wait a bit to keep from clobbering the CPU
        time.sleep(0.001)

    if data:
        print "recibo mensaje"
        print(data)
        try:
            if message['receiver'] == 'server':
                #  the /hello message announces the new client
                if ( message['message'].startswith("/hello") ):

                    outjson = {"sender": "server",
                               "receiver": "room",
                               "message": message[
                                              'sender'] + " joined the chat make them feel welcome the " + name + " admin team", \
                               "color": 31}
                    send_ack(client)
                    broadcast(json.dumps(outjson), "server")

                #  the /who message is only echoed back to the client who sent it
                #  The response is a list of other people in the chat room
                elif ( message['message'].startswith("/who") ):

                    outjson = {"sender": "server",
                               "receiver": client[0],
                               "message": "people in room: " + ", ".join([y[0] for y in clients]), \
                               "color": 31}
                    send_ack(client)
                    sock.sendto(json.dumps(outjson), client[1])

                #  The /goodbye message let's everyone know we're leaving
                elif ( message['message'].startswith("/goodbye") ):

                    outjson = {"sender": "server",
                               "receiver": "room",
                               "message": message['sender'] + " left the chat",
                               "color": 32}

                    clients.remove(client)
                    broadcast(json.dumps(outjson), "server")


            elif message['receiver'] == 'room':
                #  Message to room simply re-broadcasted back to all clients
                    outjson = {"sender": message['sender'],
                               "receiver": "room",
                               "message": message['message'],
                               "color": message['color']}
                    send_ack(client)
                    broadcast(json.dumps(outjson), message['sender'])
            else:
                #Private message
                send_ack(client)
                dest_client = next((x for x in clients if x[0] == message['receiver']), None)
                sock.sendto(json.dumps(message), dest_client[1])

            print(clients)
            # f = open("messages.txt", "a")
            # f.write(str(data) + "\n")
            # f.close()
            # a = open("clients.txt", "a")
            # a.write(str(clients) + "\n")
            # a.close()

        except ValueError:

            print("Error encountered")
