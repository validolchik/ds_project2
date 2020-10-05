import socket, os, sys
from threading import Thread


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048 # send 2048 bytes each time step


COMMAND_PORT = 3500 #port for commands from name server



class Storage(Thread):

	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def __init__(self, command_sock: socket.socket):
		super().__init__(daemon=True)
		self.command_sock = command_sock
		self.current_dir = '/var/data'#to avoid using cd


	#connection lost or closed
	def close(self):
		self.command_sock.close()
		print('Client disconected')


	#main thread
	def run(self):
		mess = self.command_sock.recv(BUFFER_SIZE).decode()
		print(mess)

	''' Create new empty file '''
	def create(self, filename):
		stream = os.popen('touch ' + self.current_dir+filename)
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
		stream = os.popen('rm ' + self.current_dir+filename)
		return stream.read()

	'''
	Provide information about the file
	'''
	def info(self, filename):
		stream = os.popen('ls -l ' + self.current_dir+filename)
		out = stream.read()
		return out

	'''
	Create a copy of file
	'''
	def copy(self, filename, newpath):
		stream = os.popen('cp '+ self.current_dir+file + ' ' + self.current_dir+newpath)
		return stream.read()

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		stream = os.popen('mv '+ self.current_dir+file + ' ' + self.current_dir+newpath)
		return stream.read()

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		#relative to current position
		if dir_path[0] == '.':
			stream = self.current_dir+dir_path
		#global path
		else:
			self.current_dir = '/var/data'+dir_path
		return stream.read()

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		stream = os.popen('ls -p '+ self.current_dir+dir_path)
		out = stream.read()
		return out
	'''
	Create new directory
	'''
	def mkdir(self, dir_path):
		stream = os.popen('mkdir '+ self.current_dir+dir_path)
		return stream.read()

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir(self, dir_path):
		stream = os.popen('rm -r '+ self.current_dir+dir_path)
		return stream.read()

	'''
	List all directories and files in the system
	'''
	def fsTree(self,):
		pass


def main(self):
	#initialize command socket and start listening
	command_sock = socket.socket()
	command_sock.bind(('', COMMAND_PORT))
	command_sock.listen()
	
	#wait for connection
	while True:
		con, addr = socket.accept()
		print(str(addr) + 'connected')
		Storage(con).start()


if __name__ == "_main_":
	main()