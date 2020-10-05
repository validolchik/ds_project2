import socket, os, sys


SEPARATOR = "<SEPARATOR>" # separator for filename and size transferring
BUFFER_SIZE = 4096 # send 4096 bytes each time step

# s = socket.socket()
# s.connect((host, port))
# s.send(f"{filename}{SEPARATOR}{filesize}".encode())
# s.sendall(bytes_read)


class Client:
	def __init__(self):
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
	def create(self):
		# i guess something like touch
		pass

	''' 
	Read file from DFS
	Download it to client host
	'''
	def read(self):
		pass

	''' 
	Upload file to DFS
	'''
	def write(self):
		pass

	''' 
	Delete existing file from DFS
	'''
	def delete(self):
		pass

	'''
	Provide information about the file
	'''
	def info(self):
		pass

	'''
	Create a copy of file
	'''
	def copy(self):
		pass

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		pass

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		pass

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		pass

	'''
	Create new directory
	'''
	def mkdir(self):
		pass

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir(self):
		pass

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

	def user_interface(self):
		# while True:
		self.list_commands()
		input_string = input("Write your command:")
		while "dfs_exit" not in input_string:
			input_string = input("Write your command:")
		answer = input("Are you sure ('y', 'n')?:")
		while answer != "n" and answer != "y":
			answer = input("write 'y' or 'n':")
		if answer == 'y':
			pass
		else:
			self.user_interface()


client = Client()
client.init()
