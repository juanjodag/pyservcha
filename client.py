#!/usr/bin/env python

import socket
import sys
import thread
import time
import json
import threading
import re

lock = threading.Lock()
server_ip = sys.argv[1]
server_port = sys.argv[2]
username = sys.argv[3]
user_regex= re.compile(r'\A@(?P<user>\S*)\s(?P<message>.*)')
command_regex = re.compile(r'\A(?P<command>/\S*)')

color = 0
allow_color = True
try:
    color = sys.argv[4]
    if color == "--nocolor":
        allow_color = False
        color = "0"
except:
    pass

sock = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
sock.settimeout(0.5)


def truncate(string, width):
    if len(string) > width:
        string = string[:width-3] + '...'
    return string

def send_with_reception_ack(message):
    global sock, username, color
    lock.acquire()
    print "Intento enviar"
    sock.sendto(json.dumps(message), (server_ip, int(server_port)))
    print "He terminado de enviar"
    try:
        print 'Receiving aknowledge for: '+str(message)
        data, addr = sock.recvfrom(1024) # buffer size is 1024 byte
        data = json.loads(data)
        print 'Ack data: '+ str(data)
        state = data['detail']
    except socket.timeout:
        print "e: Message "+"{0:<15s}".format(truncate(message['message'], 15))+" was not sent"
        state = 'Error'
    lock.release()


def get_messages():
    global sock, username, color
    while True:
        lock.acquire()
        listen_message(wait=False)
        lock.release()


def login():
    print "Please wait a moment to start chatting"
    message = {"sender": username, "receiver": "server", "message": "/hello", "color": color}
    send_with_reception_ack(message)
    listen_message(wait=True)
    message = {"sender": username, "receiver": "server", "message": "/who", "color": color}
    send_with_reception_ack(message)
    listen_message(wait=True)
    print 'You may start chatting now'


def listen_message(wait=False):
    flags = socket.MSG_DONTWAIT
    if wait:
        flags = 0
    data = None
    try:
        data, addr = sock.recvfrom(1024, flags)  # buffer size is 1024 bytes
    except socket.error:
        # wait a bit
        time.sleep(0.001)
    if data:
        #print data
        try:
            #  parse the json from the server
            message = json.loads(data)
            print message

            #  if the message is from us, then ignore it
            if message['sender'] != username:
                msg_str = message['message']

                #  if there is no user name, don't display it
                if message['sender']:
                    msg_str = message['sender'] + ": " + msg_str

                # Private message for us
                if message['receiver'] == username:
                    msg_str = "::" + message['sender'] + ":: " + message['message']

                #  print the message, with colors :) if allowed
                if len(message['message']) > 0:
                    if allow_color:
                        ts = time.strftime("%I:%M%p %S", time.localtime(time.time()))
                        print("[%s] \033[%sm%s\033[0m" % (ts, message['color'], msg_str))
                    else:
                        ts = time.strftime("%I:%M%p %S", time.localtime(time.time()))
                        print("[%s] %s" %(ts, msg_str))
        except ValueError:
            print("error: tried to decode invalid JSON data")

def get_input():
    global sock, username, color
    #  upon "connecting", send /hello and /who to announce our arrival and get a list
    #  of other people in the room
    login()
    try:
        while True:
            user_input = raw_input().strip()
            receiver = "room"
            # Sending private message
            is_private = user_regex.match(user_input)
            is_command = command_regex.match(user_input)
            if is_private:
                user_input = is_private.group('message')
                receiver = is_private.group('user')
            elif is_command:
                user_input = is_command.group('command')
                receiver = "server"

            message = {"sender": username, "receiver": receiver, "message": user_input, "color": color}

            send_with_reception_ack(message)

    except KeyboardInterrupt:
        print("byebye now")

thread.start_new_thread(get_input, ())
thread.start_new_thread(get_messages, ())

try:
    while 1:
        time.sleep(0.001)
except KeyboardInterrupt:
    print("bye")
    message = {"sender": username, "receiver": "server", "message": "/goodbye", "color": color}
    sock.sendto(json.dumps(message), (server_ip, int(server_port)))
    sys.exit(0)

