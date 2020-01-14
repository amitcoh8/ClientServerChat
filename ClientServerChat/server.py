import socket, selectors, types, os, time
from threading import Thread

class Server:

	def __init__(self,sock,host,port):
		self.sock = sock
		self.host = host
		self.port = port
		self.selector = selectors.DefaultSelector()

	def run(self):
		ClientCommunication.Connection.create_endpoint(self)
		try:
			while True:
				events = self.selector.select(timeout=None)
				for key, mask in events:
					if key.data is None:
						ClientCommunication.Connection.accept_new_client(self,key.fileobj)
					else:
						logs = ClientCommunication.Connection.service_existing_client(self,key,mask)
						if logs:
							for log in logs:
								print(log)
			print(Messages.server_closed())
		except:
			print(Messages.server_closed())

class ClientCommunication:

	class Connection:

		@staticmethod
		def create_endpoint(server):
			""" Creates server's 'docking point'. After this function initialises clients can connect to the server """
			server.sock.bind((server.host, server.port)) 
			server.sock.listen()
			server.sock.setblocking(False)
			server.selector.register(server.sock, selectors.EVENT_READ, data=None)
			timer_thread = Thread(target = ClientCommunication.Connection.set_clients_timer, args=[server.selector])
			timer_thread.start()

		@staticmethod
		def set_clients_timer(selector):
			""" Iterates over all of the registerd users in the system. If user has passed the time limit, function disconnects him from the server """
			while True:
				users_to_delete = []
				time.sleep(1)
				for username in ClientsData._timer_dict:
					timer = ClientsData.get_timer(username) 
					timer = timer +1
					if (timer >= 60):
						ClientCommunication.Connection.disconnect_client(selector,username)
						users_to_delete.append(username)
					else:
						ClientsData.set_timer(username,timer)
				if users_to_delete:
					ClientsData.delete_users(users_to_delete)

		@staticmethod
		def accept_new_client(server, client_sock):
			""" Initialises new client socket connection to the server. """
			client, address = client_sock.accept()
			client.setblocking(False)
			data = types.SimpleNamespace(address=address, outb=b'')
			events = selectors.EVENT_READ
			server.selector.register(client,events,data=data)

		@staticmethod
		def service_existing_client(server, key, mask):
			""" Checks if a connected client sends message request to server. If he does, function initialises read event action. """
			client_sock = key.fileobj
			data = key.data
			if mask & selectors.EVENT_READ:
				return ClientCommunication.Recieiving.read_event(server,client_sock,data)

		@staticmethod
		def disconnect_client(selector,username):
			""" Disconnects user from event regestration and delets it from DB. """
			print(Messages.disconnecting_user(username))
			ClientCommunication.Sending.send_to_user(username,Parse.ServerToClient.to_message_format(Messages.bye()))
			client_sock = ClientsData.get_sock(username)
			selector.unregister(client_sock)
			client_sock.close()

	class Recieiving:

		@staticmethod
		def read_event(server,client_sock, data):
			message = client_sock.recv(1024)
			if message:
				data.outb += message
				message = message.decode("utf-8")
				return Parse.ClientToServer.handle_message(server,client_sock, message)

	class Registration:

		def register(client_sock,message):
			register_info = Parse.ClientToServer.to_register_info(message)
			registered = ClientsData.register_client(register_info[1],client_sock)
			if registered == True:
				ClientCommunication.Sending.send_to_sock(client_sock,register_info[0] + Messages.registered_successfully())
				succession_log = Messages.user_registered(register_info[0],register_info[1], client_sock.getpeername())
				return [succession_log]
			else:
				exception_log = Messages.ex_username_taken(register_info[1]) 
				ClientCommunication.Sending.send_to_sock(client_sock, Parse.ServerToClient.to_exception_format(exception_log))
				return [exception_log]	

	class Sending:

		def _distribute(data_from_client):
			logs = []
			for user in data_from_client[2]:
				client_message = f"'({data_from_client[0]}) {data_from_client[1]}': {data_from_client[3]}"
				ClientCommunication.Sending.send_to_user(user,Parse.ServerToClient.to_message_format(client_message))
				logs.append(Messages.message_sent(user,client_message))
			return logs

		def _inform_if_no_user(receivers,sender):
			exceptions = []
			flag = True
			for receiver in receivers:
				if not ClientsData.does_user_exist(receiver):
					flag = False
					exception = Messages.ex_user_doesnt_exist(receiver)
					ClientCommunication.Sending.send_to_user(sender, Parse.ServerToClient.to_exception_format(exception))	
					exceptions.append(exception)
			return exceptions
			
		@staticmethod
		def send_to_user(user_to, message):
			sock = ClientsData.get_sock(user_to)
			ClientCommunication.Sending.send_to_sock(sock,message)

		@classmethod
		def send_to_sock(cls,sock,message):
			if sock:
				sock.sendall(bytes((message),"utf-8"))

		@classmethod
		def try_distribute(cls,client_message):
			data_from_client = Parse.ClientToServer.to_message_info(client_message)
			ClientsData.set_timer(data_from_client[1],0)
			exceptions = cls._inform_if_no_user(data_from_client[2],data_from_client[1])
			if not exceptions: 
				logs = cls._distribute(data_from_client)
				return logs
			else:
				return exceptions
			
class Parse:

	class ClientToServer:

		def _is_register_type(message):
			if message[0] == "r":
				return True
			else:
				return False

		def _is_message_type(message):
			if message[0] == "m":
				return True
			else:
				return False

		@staticmethod
		def to_content(message):
			""" Gets a message from client
			Returns message's content """
			return message.split(" - ",1)[1]

		@classmethod
		def to_register_info(cls,message):

			""" Gets a client-to-client message
			Returns a list of [sender,users,content] """ 
			data = cls.to_content(message)
			info = data.split(" ^ ")
			cur_time = info[0]
			sender = info[1]
			return [cur_time,sender]

		@classmethod
		def to_message_info(cls,message):

			""" Gets a client-to-client message
			Returns a list of [current_time,sender,receivers,message] """ 
			data = cls.to_content(message).split(" * ",1)
			message = data[1]
			data = data[0].split(" $ ")
			receivers = data[1].split()
			data = data[0].split(" ^ ")
			sender = data[1]
			cur_time = data[0]
			return [cur_time,sender,receivers,message]

		@classmethod
		def handle_message(cls,server,client_sock,message):

			""" Gets a message from client 
			Identifies the message type and calls the appropriate function
		    returns log """

			if cls._is_register_type(message):
				return ClientCommunication.Registration.register(client_sock,message)
			elif cls._is_message_type(message):
				return ClientCommunication.Sending.try_distribute(message) 

	class ServerToClient:

		@staticmethod
		def to_message_format(message):
			""" Gets a client-to-server message
			Retruns it formatted to message type """
			return f"m {message}"

		@staticmethod
		def to_exception_format(message):
			""" Gets a server-to-client message
			Retruns it formatted to exception type """
			return f"e {message}"

class ClientsData:
    
	_socket_dict = dict()
	_timer_dict = dict()

	@classmethod
	def register_client(cls,username,sock):
		""" Gets username and socket. Inserts them into dictionary as Key-Value Pair [username, sock] """
		if username not in cls._socket_dict:
			cls._socket_dict[username] = sock
			cls._timer_dict[username] = 0
			return True
		else:
			return False

	@classmethod 
	def set_timer(cls,username,timer):
		cls._timer_dict[username] = timer

	@classmethod 
	def get_timer(cls,username):
		return cls._timer_dict.get(username, None)

	@classmethod
	def delete_user(cls,username):
		if username in cls._socket_dict and username in cls._timer_dict:
			del cls._timer_dict[username]
			del cls._socket_dict[username]

	@classmethod
	def delete_users(cls,usernames):
			for username in usernames:
				cls.delete_user(username)

	@classmethod
	def get_sock(cls,username):
		return cls._socket_dict.get(username, None)

	@classmethod
	def does_user_exist(cls,username):
			if username in cls._socket_dict:
				return True
			else:
				return False

class Messages:
	
	_REGISTERED = "Registered successfully!"
	_BYE = "bye"
	_SER_CLOSED = "Server has closed!"
	_SER_ERROR = "Error! Server error!"
		
	@staticmethod
	def user_registered(time,username,address):
		return f"({time}) User {username} {address} has registerd to the server!"

	@classmethod
	def registered_successfully(cls):
		return cls._REGISTERED

	@classmethod
	def server_closed(cls):
		return cls._SER_CLOSED

	@staticmethod
	def message_sent(username, message):
		return f"{message} -> '{username}'"

	@staticmethod
	def disconnecting_user(username):
		return f"Disconnecting user '{username}'"
	
	@classmethod
	def bye(cls):
		return cls._BYE

	@staticmethod
	def ex_username_taken(username):
		return f"Error! Username '{username}' is taken!"

	@staticmethod
	def ex_user_doesnt_exist(username):
		return f"Error! User '{username}' does not exist!"

	@classmethod
	def ex_error(cls):
		return cls._SER_ERROR

server = Server(socket.socket(socket.AF_INET,socket.SOCK_STREAM), '127.0.0.1', 1024)
server.run()






