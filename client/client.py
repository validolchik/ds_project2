import socket


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 4096 # send 4096 bytes each time step



# s = socket.socket()
# s.connect((host, port))
# s.send(f"{filename}{SEPARATOR}{filesize}".encode())
# s.sendall(bytes_read)


class Client:
	def __init__(self):
		self.connect_to_name_server()
		self.init()

	def connect_to_name_server(self):
		pass

	"""
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size
	"""
	def init(self):
		print("init")
		self.user_interface()
		pass

	''' Create new empty file '''
	def create(self, filename):
		print("create called")
		# i guess something like touch
		# pass

	''' 
	Read file from DFS
	Download it to client host
	'''
	def read(self, filename):
		print("read called")

	''' 
	Upload file to DFS
	'''
	def write(self, filename):
		print("write called")

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
			  "Read directory - 'ls {directory}'\n"
			  "Make directory - 'mkdir {directory}'\n"
			  "Delete directory - 'deldir {directory}'\n"
			  "List available commands - 'commands'\n"
			  "Exit - dfs_exit")

	def process_command(self, command):
		types = {'create': 'create',
				 'read': 'read',
				 'write': 'write',
				 'delete': 'delete',
				 'info':'info',
				 'copy': 'copy',
				 'move': 'move',
				 'cd': 'opendir',
				 'ls': 'readdir',
				 'mkdir':'mkdir',
				 'deldir': 'deldir',
				 'commands': 'user_interface',
				 'init': 'init'
				 }
		mes = command.split(' ')
		print(mes)
		rtype = mes[0]
		res = 0
		if len(mes) == 1:
			# res = types[mes[0]]()
			res = getattr(self, types[mes[0]])()
		elif len(mes) == 2:
			# res = types[mes[0]](mes[1])
			res = getattr(self, types[mes[0]])(mes[1])
		elif len(mes) == 3:
			res = getattr(self, types[mes[0]])(mes[1], mes[2])
			# res = types[mes[0]](mes[1], mes[2])
		# lenght = len(res)
		# return rtype, lenght, res


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
			exit()
		else:
			self.user_interface()


def main():
	socket = socket.socket()

	host = "0.0.0.0"
	port = 3425

	print(f"[+] Connecting to {host}:{port}")
	socket.connect((host, port))
	print("[+] Connected.")
	client = Client()
	client.init()


if __name__ == "__main__":
	main()
