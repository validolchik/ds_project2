import socket, os, sys


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 4096 # send 4096 bytes each time step

# s = socket.socket()
# s.connect((host, port))
# s.send(f"{filename}{SEPARATOR}{filesize}".encode())
# s.sendall(bytes_read)

class NameServer():
	
	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def __init__(self):
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


