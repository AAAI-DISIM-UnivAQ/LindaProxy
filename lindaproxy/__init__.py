'''

LindaProxy
 module to encapsulate DALI agent communication
 in the ASP solver case study
 Licensed with Apache Public License
 by AAAI Research Group
 Department of Information Engineering and Computer Science and Mathematics
 University of L'Aquila, ITALY
 http://www.disim.univaq.it

'''

import socket

import re

import sys
import asyncio
import asyncio.streams

def param_get(message):
    if message[:2] == "S:":
        n_param = ord(message[3])
        init = 4
        fres = ""
        for _ in range(n_param):
            res, l = param_get(message[init:])
            init += l
            fres += res + ":"
        fres = fres[:-1]
        return fres, init
    elif message[0] == "S":
        name = message[1:].split(chr(0), 1)[0]
        n_param = ord(message[len(name) + 2])
        init = len(name) + 3

        fres = name + "("
        for _ in range(n_param):
            res, l = param_get(message[init:])
            init += l
            fres += res + ","
        fres = fres[:-1] + ")"
        return fres, init
    elif message[0] == "A" or message[0] == "I":
        param = message.split(chr(0))[0]
        return param[1:], len(param) + 1
    elif message[0] == "[" or message[0] == "]" or message[0] == '"':
        fres = ""
        init = 0
        while message[init] == "[" or message[init] == '"':
            if message[init] == "[":
                res, l = param_get(message[init + 1:])
                fres += res + ","
                init += l + 1
            else:
                init += 1
                while ord(message[init]) != 0:
                    fres += str(ord(message[init])) + ","
                    init += 1
                init += 1
        return '['+fres[:-1]+']', init + 1
    else:
        print('def', message)
        return "$$", 1

def read_message(message):
    res, length = param_get(message[3:])
    return res

utils = {
    'charSeparator': '\x00'
}
def spitParameters(par, sep):
    block = 0
    param = ""
    parameters = []
    for x in par:
        if x == sep and block == 0:
            parameters.append(param.strip())
            param = ""
        else:
            if x == '(' or x == "[":
                block += 1
            elif x == ')' or x == "]":
                block -= 1
            param += x
    if param.strip() != "":
        parameters.append(param.strip())
    return parameters
utils['spitParameters'] = spitParameters
regex = {
    'atomo': re.compile(r'^([a-z0-9 _\-\.]+)$', re.IGNORECASE),
    'funzione': re.compile(r'^[a-z0-9_]+[ ]*\((.*)\)[ ]*$', re.IGNORECASE),
    'lista': re.compile(r'^[ ]*\[(.*)\][ ]*$', re.IGNORECASE),
    'tupla': re.compile(
        r'^(([a-z0-9 _\-\.]+|[a-z0-9_\-\.]+[ ]*\([a-z 0-9\-\._\:\(\)\[\]\,]*\)[ ]*|[ ]*\[[a-z 0-9_\-\.\:\(\)\[\]\,]*\][ ]*)\:)+([a-z0-9 _\-\.]+|[a-z0-9_]+[ ]*\([a-z 0-9_\-\.\:\(\)\[\]\,]*\)[ ]*|[ ]*\[[a-z 0-9_\-\.\:\(\)\[\]\,]*\][ ]*)$',
        re.IGNORECASE
    )
}
utils['regex'] = regex

def new_get_args(m):
    m = m.strip()
    ser = regex['atomo'].match(m)
    if ser is not None:
        atomo = ser.group(0)
        if str(atomo).isnumeric():
            return "I"+atomo+'\x00'
        else:
            return "A"+atomo+'\x00';
    ser = regex['funzione'].match(m)
    if ser is not None:
        name = "S" + m[:m.index("(")]+"\x00"

        body_result = ""
        params = utils['spitParameters'](ser.group(1), ',')
        for par in params:
            body_result += new_get_args(par)

        return name + chr(len(params))+body_result
    ser = regex['lista'].match(m)
    if ser is not None:
        result = ""
        params = utils['spitParameters'](ser.group(1), ',')

        special_int = False
        for par in params:
            # print par
            if len(par) == 1 and str(par).isnumeric() and int(par) > 0:
                if not special_int:
                    result += '"'
                special_int = True
                result += chr(int(par))
            else:
                if special_int:
                   result += '\x00'
                special_int = False
                result += '[' + new_get_args(par)
        if special_int:
           result += '\x00'
        return result + ']'

    ser = regex['tupla'].search(m)
    if ser is not None:
        result = "S:\x00"
        params = utils['spitParameters'](m, ':')

        result += chr(len(params))
        for par in params:
            result += new_get_args(par)
        return result
    print('shame..', m)
    return ""

def write_message(message):
    res = "foD" + new_get_args(message)
    return res

__all__ = ["write_message", "read_message"]

class LindaProxy(object):

    def __init__(self, host='localhost', port=3010):
        self._host = host
        self._port = port
        self._LindaSocket = socket.socket()
        self._LindaSocket.connect((self._host, self._port))
        self._loop = None
        self._proxy = None

    def createmessage(self, senderAg, destinationAg, typefunc, message):
        m = "message(%s:3010,%s,%s:3010,%s,italian,[],%s(%s,%s))" % \
            ('localhost', destinationAg, self._host, senderAg,
              typefunc, message, senderAg)
        return m

    def send_message(self, destAg, termPl):
        msg = self.createmessage('user', destAg, 'send_message', termPl)
        wrm = write_message(msg)
        self._LindaSocket.send(bytes(wrm, encoding='utf-8'))


    def start(self, host='localhost', port=3011):
        self._loop = asyncio.get_event_loop()
        # creates a server and starts listening to TCP connections
        self._proxy = MyServer()
        self._proxy.start(self._loop, host, port)
        self._loop.run_forever()

    def stop(self):
        self._proxy.stop(self._loop)







class MyServer:
    """
    This is just an example of how a TCP server might be potentially
    structured.  This class has basically 3 methods: start the server,
    handle a client, and stop the server.
    Note that you don't have to follow this structure, it is really
    just an example or possible starting point.
    """

    def __init__(self):
        self.server = None # encapsulates the server sockets

        # this keeps track of all the clients that connected to our
        # server.  It can be useful in some cases, for instance to
        # kill client connections or to broadcast some data to all
        # clients...
        self.clients = {} # task -> (reader, writer)

    def _accept_client(self, client_reader, client_writer):
        """
        This method accepts a new client connection and creates a Task
        to handle this client.  self.clients is updated to keep track
        of the new client.
        """

        print("New client", client_reader, client_writer)
        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader, client_writer))
        self.clients[task] = (client_reader, client_writer)

        def client_done(task):
            print("client task done:", task, file=sys.stderr)
            del self.clients[task]

        task.add_done_callback(client_done)

    @asyncio.coroutine
    def _handle_client(self, client_reader, client_writer):
        """
        This method actually does the work to handle the requests for
        a specific client.  The protocol is line oriented, so there is
        a main loop that reads a line with a request and then sends
        out one or more lines back to the client with the result.
        """
        while True:
            data = (yield from client_reader.readline()).decode("utf-8")
            if not data: # an empty string means the client disconnected
                break
            cmd, *args = data.rstrip().split(' ')
            if cmd == 'add':
                arg1 = float(args[0])
                arg2 = float(args[1])
                retval = arg1 + arg2
                client_writer.write("{!r}\n".format(retval).encode("utf-8"))
            elif cmd == 'repeat':
                times = int(args[0])
                msg = args[1]
                client_writer.write("begin\n".encode("utf-8"))
                for idx in range(times):
                    client_writer.write("{}. {}\n".format(idx+1, msg)
                                        .encode("utf-8"))
                client_writer.write("end\n".encode("utf-8"))
            else:
                print("Bad command {!r}".format(data), file=sys.stderr)

            # This enables us to have flow control in our connection.
            yield from client_writer.drain()

    def start(self, loop, host, port):
        """
        Starts the TCP server, so that it listens on port 'port'.
        For each client that connects, the accept_client method gets
        called.  This method runs the loop until the server sockets
        are ready to accept connections.
        """
        print('Listening on port', port)
        self.server = loop.run_until_complete(
            asyncio.streams.start_server(self._accept_client,
                                         host, port,
                                         loop=loop))

    def stop(self, loop):
        """
        Stops the TCP server, i.e. closes the listening socket(s).
        This method runs the loop until the server sockets are closed.
        """
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None


def main():
    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = MyServer()
    server.start(loop)

    @asyncio.coroutine
    def client():
        reader, writer = yield from asyncio.streams.open_connection(
            '127.0.0.1', 12345, loop=loop)

        def send(msg):
            print("> " + msg)
            writer.write((msg + '\n').encode("utf-8"))

        def recv():
            msgback = (yield from reader.readline()).decode("utf-8").rstrip()
            print("< " + msgback)
            return msgback

        # send a line
        send("add 1 2")
        msg = yield from recv()

        send("repeat 5 hello")
        msg = yield from recv()
        assert msg == 'begin'
        while True:
            msg = yield from recv()
            if msg == 'end':
                break

        writer.close()
        yield from asyncio.sleep(0.5)

    # creates a client and connects to our server
    try:
        loop.run_until_complete(client())
        server.stop(loop)
    finally:
        loop.close()


if __name__ == '__main__':
    main()
