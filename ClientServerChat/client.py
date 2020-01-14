import socket,sys,pathlib, datetime, os
from threading import Thread

class Client:

    def __init__(self,sock,host,port):
        self.sock = sock
        self.host = host
        self.port = port
        self.username = ""

    def run(self):
        ServerCommunication.Connection.connect(self)
        ServerCommunication.Registration.register(self)
        # Opens a thread for displaying received messages from the server
        display_thread = Thread(target = ServerCommunication.Recieiving.log_received, args=[self])
        display_thread.start()
        # Main loop for reading console input messages and sending to the server
        while True:
            ServerCommunication.Sending.to_other_client(self)

class ServerCommunication:

    class Connection:

        @staticmethod
        def connect(client):
            """ Connects client to server. """
            client.sock.connect((client.host,client.port))

    class Registration:

        @staticmethod
        def _try_register(client):
            """ Tries to register client to the server.
            If succeeded returns True, else returns the appropriate exception.  """
            
            file = Input.Read.username_from_file("CONFIG.config")
            if file:
                username = file
                print(Messages.welcome())
            else:
                print(Messages.register())
                username = Input.Read.keyboard()

            if not Input.Validate.username(username):
                return Messages.ex_username_format
            else:
                ServerCommunication.Sending.to_server(client,Parse.ClientToServer.to_register_command(username))

            server_response = ServerCommunication.Recieiving.receive_message(client)
            if Parse.ServerToClient.is_error(server_response):
               return Parse.ServerToClient.to_content(server_response)

            else:
                client.username = username
                return True

        @staticmethod 
        def register(client):
            """ Registers client to the server. Tries to register recursively until success. """
            registration = ServerCommunication.Registration._try_register(client)

            if registration != True:
               print(registration)
               ServerCommunication.Registration.register()
            else:
               print(Messages.registered())

    class Recieiving:

        @staticmethod
        def receive_message(client):
            """ Receives message from server. Returns outcome. """
            try:
                message = client.sock.recv(1024)
                message = message.decode("utf-8")
                return message
            except:
                message = ""
                return message

        @staticmethod
        def log_received(client):
            """ If received, logs a message from server. """
            while True:
                message = ServerCommunication.Recieiving.receive_message(client)
                content = Parse.ServerToClient.to_content(message)
                if content:
                    print(content)

    class Sending:

        @staticmethod
        def to_server(client, message):
            if client.sock:
                client.sock.sendall(bytes(message,"utf-8"))

        @staticmethod
        def to_other_client(client):
            """ Gets input from client. Sends it to server if formatted properly. """
            clients_list = Input.Read.keyboard()
            if Input.Validate.usernames(clients_list):
               message = Input.Read.keyboard()
               parsed_message = Parse.ClientToServer.to_send_command(client.username,clients_list,message)
               ServerCommunication.Sending.to_server(client,parsed_message)
            else:
                print(Messages.ex_username_format())

class Input:
    
    class Validate:

        @staticmethod
        def username(u_name):
            """ Checks weather username is formatted properly: contains only letters with not spaces. Returns bool """
            if u_name.isalpha():
                return True
            else:
                return False

        @staticmethod
        def usernames(u_names):
            """ Checks weather all usernames are formatted properly. Returns bool """
       
            flag = True
            for client in u_names.split():
                if not Input.Validate.username(client):
                    flag = False
                    break
            return flag

    class Read:

        def keyboard():
            return input()
        
        def username_from_file(filepath):
            if os.path.exists(filepath):
                username = open(filepath, "r")
                username = username.readline()
                if username:
                    return username
            return ""

class Parse:

    class ClientToServer:

        def _time():
            return datetime.datetime.now()

        @classmethod
        def to_register_command(cls,username):
            now = cls._time()
            """ Gets a client-to-server message. Retruns it formatted to register command. """
            return f"r - {now.hour}:{now.minute} ^ {username}"

        @classmethod
        def to_send_command(cls,username, clients_list, message):
            """ Gets a client-to-server message. Retruns it formatted to message command.  """
            now = cls._time()
            return f"m - {now.hour}:{now.minute} ^ {username} $ {clients_list} * {message}"

    class ServerToClient:

        @staticmethod
        def _to_data_format(message):
            """ Gets a server-to-client message. Retruns a list of [message_type,content] """
            if message:
                parsed_message = message.split(" ",1)
                return parsed_message
            return message

        @staticmethod
        def is_error(message):
            """ Gets a server-to-client message. checks if message is of error type.
            returns Bool """
            if message:
                parsed_message = Parse.ServerToClient._to_data_format(message)
                if parsed_message[0][0] == "e":
                    return True
                else:
                    return False
            return False

        @staticmethod
        def to_content(message):
            """ Gets a server-to-client message. returns message content """ 
            if message:
                parsed_message = Parse.ServerToClient._to_data_format(message)
                return parsed_message[1]
            return message

class Messages:
    
    _REGISTER = "Please register with your username: "
    _REGISTERED = "Registered successfully!"
    _EX_USERNAME_FORMAT = "Error! Usernames must contain letters only with no spaces."

    @classmethod
    def register(cls):
        return cls._REGISTER

    @classmethod
    def registered(cls):
        return cls._REGISTERED

    @classmethod
    def ex_username_format(cls):
        return cls._EX_USERNAME_FORMAT

    @staticmethod
    def welcome(username):
        return f"Welcome {username}"

client = Client(socket.socket(socket.AF_INET,socket.SOCK_STREAM), '127.0.0.1', 1024)
client.run()













