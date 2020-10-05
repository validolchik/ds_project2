import socket, os, sys
from threading import Thread


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048 # send 2048 bytes each time step


COMMAND_PORT = 3500
UP_PORT = 3501
DOWN_PORT = 3502
SHARE_PORT = 3503
# s = socket.socket()
# s.connect((host, port))
# s.send(f"{filename}{SEPARATOR}{filesize}".encode())
# s.sendall(bytes_read)

class Storage(Thread):

	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def __init__(self):
		os.system('cd /var/data')

	''' Create new empty file '''
	def create(self, filename):
		stream = os.popen('touch ' + filename)
		return stream.read()

	''' 
	Read file from DFS
	Download it to client host
	'''
	def download(self, filename):
		pass

	''' 
	Upload file to DFS
	'''
	def upload(self, filename):
		pass

	''' 
	Delete existing file from DFS
	'''
	def delete(self, filename):
		stream = os.popen('rm ' + filename)
		return stream.read()

	'''
	Provide information about the file
	'''
	def info(self, filename):
		stream = os.popen('ls -l ' + filename)
		out = stream.read()
		return out

	'''
	Create a copy of file
	'''
	def copy(self, filename, newpath):
		stream = os.popen('cp '+ file + ' ' + newpath)
		return stream.read()

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		stream = os.popen('mv '+ file + ' ' + newpath)
		return stream.read()

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		stream = os.popen('cd ' + dir_path)
		return stream.read()

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		stream = os.popen('ls -p '+dir_path)
		out = stream.read()
		return out
	'''
	Create new directory
	'''
	def mkdir(self, dir_path):
		stream = os.popen('mkdir '+dir_path)
		return stream.read()

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir(self, dir_path):
		stream = os.popen('rm -r '+dir_path)
		return stream.read()

	def fsTree(self,):
		pass