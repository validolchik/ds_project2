import socket
import os

SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048 # send 4096 bytes each time step



# s = socket.socket()
# s.connect((host, port))
# s.send(f"{filename}{SEPARATOR}{filesize}".encode())
# s.sendall(bytes_read)


class Client:
	def __init__(self):
		# self.connect_to_name_server('localhost', 6235)
		self.command_socket = self.connect_to_server('192.168.1.33', 6235)
		self.user_interface()
	
	'''
	connect to server by his ip and port number
	'''
	
	def connect_to_server(self, server_ip, server_port):
		s = socket.socket()

		# name server's host and port
		# host = "188.130.155.153"
		# host = 'localhost'
		# port = 6235

		print(f"[+] Connecting to {server_ip}:{server_port}")
		s.connect((server_ip, server_port))
		print("[+] Connected.")
		return s

	"""
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size
	"""
	def init(self):
		print("init")
		req = self.make_req('init')
		self.command_socket.send(req)
		resp = self.get_response(self.command_socket, 'init')
		print("init " + str(resp))

	def remove_all_existing_files(self):
		return None

	'''
	build and pad a request with given fields
	'''
	def make_req(self, *args):
		fields = list(args)
		res = ''
		for f in fields:
			res += f + SEPARATOR
		res += ' ' * (BUFFER_SIZE - len(res))
		return res.encode('utf-8')

	'''
	Get response and extract body
	'''
	def get_response(self, sock, rtype):
		resp = sock.recv(len(rtype)+len(SEPARATOR)+1).decode('utf-8')
		while resp[-2] + resp[-1] != SEPARATOR:
			resp += sock.recv(1).decode('utf-8')
		lenght = int(resp.split(SEPARATOR)[1])
		resp = sock.recv(lenght).decode('utf-8')
		return resp


	''' Create new empty file '''
	def create(self, filename):
		print("create called")
		req = self.make_req('crf', filename)
		self.command_socket.send(req)
		resp = self.get_response(self.command_socket, 'crf')
		print("create " + str(resp))


	''' 
	Read file from DFS
	Download it to client host
	'''
	def read(self, filename):
		print("read called")
		req = self.make_req('rdf', filename)
		self.command_socket.send(req)

		storage_port, filesize = self.get_response(self.command_socket, 'rdf').decode('utf-8').split(SEPARATOR)
		if int(storage_port):
			self.command_socket.send('y'.encode('utf-8'))
			storage_port = int(storage_port)
		else:
			return "error"

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('', storage_port))
		sock.listen()

		storage_socket, address = sock.accept()

		file_size = int(filesize)

		# caculate number of 2KB chunks in the file
		# and size of remaining data
		n_blocks = file_size // BUFFER_SIZE
		extra_block = file_size - n_blocks * BUFFER_SIZE

		f = open(filename, 'wb')

		for i in range(n_blocks):
			block = storage_socket.recv(BUFFER_SIZE)
			f.write(block)

		block = storage_socket.recv(extra_block)
		f.write(block)
		f.close()
		resp = self.get_response(self.command_socket, 'wrf')
		
		sock.close()
		storage_socket.close()
		return resp


	''' 
	Upload file to DFS
	'''
	def write(self, filename):
		print("write called")
		file_size = os.path.getsize(filename)
		req = self.make_req('wrf', filename, str(file_size))
		self.command_socket.send(req)

		# resp = self.get_response(self.command_socket, 'wrf')
		resp = self.command_socket.recv(4)
		storage_port = resp.decode('utf-8')
		if int(storage_port):
			self.command_socket.send('e'.encode('utf-8'))
			storage_port = int(storage_port)
		else:
			print("error in writing")
			return "error"

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('', storage_port))
		sock.listen()

		storage_socket, address = sock.accept()

		# calculate number of 2KB chunks in the file
		# and size of remaining data
		n_blocks = file_size // BUFFER_SIZE
		extra_block = file_size - n_blocks * BUFFER_SIZE

		# send parts of size BUFFERSIZE to storage
		f = open(filename, 'rb')
		for i in range(n_blocks):
			block = f.read(BUFFER_SIZE)
			storage_socket.send(block)

		# send remaining part of file
		extra_block = f.read(extra_block)
		storage_socket.send(extra_block)
		f.close()
		
		resp = self.get_response(self.command_socket, 'wrf')

		sock.close()
		storage_socket.close()
		return resp


	''' 
	Delete existing file from DFS
	'''
	def delete(self, filename):
		print("delete called")

	'''
	Provide information about the file
	'''
	def info(self, filename):
		print("info called")

	'''
	Create a copy of file
	'''
	def copy(self, filename):
		print("copy called")

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		print("move called")

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		print("openddir called")

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		print("readdir called")

	'''
	Create new directory
	'''
	def mkdir(self, dir_name):
		print("mkdir")

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir(self, dirname):
		print("deldir")

	def list_commands(self):
		print("List of available commands with short description:")
		print("Initialize - 'init'\n"
			  "Create empty file - 'create {filename}'\n"
			  "Read file (download) - 'read {filename}'\n"
			  "Write file (upload) - 'write {filename}'\n"
			  "Delete file - 'delete {filename}'\n"
			  "File info - 'info {filename}'\n"
			  "Copy file - 'copy {filename}'\n"
			  "File move - 'move {filename} {destination_path}'\n"
			  "Open directory - 'cd {directory}'\n"
			  "Read current directory - 'ls'\n"
			  "Make directory - 'mkdir {directory}'\n"
			  "Delete directory - 'deldir {directory}'\n"
			  "List available commands - 'commands'\n"
			  "Exit - dfs_exit")

	def process_command(self, command):
		types = {'create': 'crf',
				 'read': 'read',
				 'write': 'write',
				 'delete': 'rmf',
				 'info':'inf',
				 'copy': 'cpf',
				 'move': 'mvf',
				 'cd': 'opdir',
				 'ls': 'rddir',
				 'mkdir':'mkdir',
				 'deldir': 'rmdir',
				 'commands': 'user_interface',
				 'init': 'init'
				 }
		mes = command.split(' ')
		print(mes)
		# check if command in the commands list
		if not mes[0] in types:
			print("Write command from command list")
			self.user_interface()
		elif mes[0] == 'read' or mes[0] == 'write':
			res = getattr(self, types[mes[0]])(mes[1])
		else:
			req = None
			if len(mes) == 1:
				# res = getattr(self, types[mes[0]])()
				req = self.make_req(types[mes[0]])
			elif len(mes) == 2:
				# res = getattr(self, types[mes[0]])(mes[1])
				req = self.make_req(types[mes[0]], mes[1])
			elif len(mes) == 3:
				req = self.make_req(types[mes[0]], mes[1], mes[2])
				# res = getattr(self, types[mes[0]])(mes[1], mes[2])
			self.command_socket.send(req)
			resp = self.get_response(self.command_socket, types[mes[0]])
			print(resp)


	def user_interface(self):
		self.list_commands()
		input_string = input("Write your command:")
		while input_string != "dfs_exit":
			self.process_command(input_string)
			input_string = input("Write your command:")
		answer = input("Are you sure ('y', 'n')?:")
		while answer != "n" and answer != "y":
			answer = input("write 'y' or 'n':")
		if answer == 'y':
			req = self.make_req('exit')
			self.command_socket.send(req)
			exit()
		else:
			self.user_interface()


def main():
	client = Client()
	# client.init()


if __name__ == "__main__":
	main()
