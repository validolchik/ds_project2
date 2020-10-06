import socket, os, sys
from threading import Thread
import time

SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048

CLIENT_PORT = 6235
COMMAND_PORT = 3500
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502#port to listen broadcasts response
HOST = '0.0.0.0'

class NameServer():

	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	#TODO


	'''
	start storage discovery thread
	'''
	def __init__(self):
		explorer = Thread(target = self.explorer, daemon=True)
		explorer.start()


	'''
	perform perodic(30sec) storage rediscovery

	might result in having to redo the messages
	'''
	def explorer(self):
		listener = Thread(target = self.listen, daemon=True)
		self.discover()
		while True:
			time.sleep(30)
			self.discover()

	'''
	Listen for replies to a broadcast
	'''
	def listen(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('', DISCOVER_RESPONSE_PORT))
		while True:
			data, addr = sock.recvfrom(BUFFER_SIZE)
			host, port = addr
			self.host_discovered(host)

	'''
	add discovered host to the list of alive storages
	'''
	def host_discovered(self, host):
		if host not in self.storages:
			self.storages.append(host)
		
	'''
	empty list of alive storages and 
	broadcast a discovery message
	'''
	def discover(self):
		self.storages = []
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.sendto(b'discovery', ('<broadcast>', DISCOVER_PORT))


	def connect(self, sock:socket.socket):
		self.sock = sock

	#connection lost or closed
	def close(self):
		self.sock.close()
		print('Client disconected')

	def run(self):
		pass


	'''
	parse and execute the message
	'''
	def parse(self, message):
		#dictionary with all possible functions
		types ={'crf':self.create,
				'cpf':self.copy,
				'mvf':self.move,
				'rmdir':self.deldir,
				'mkdir':self.mkdir,
				'opdir':self.opendir,
				'down':self.download,
				'up':self.upload
				}

		#split message and get request type
		mes = message.split(SEPARATOR)
		rtype = mes[0]
		
		res = 0
		#execute function with needed amount of arguments
		if len(mes) == 1:
			res = types[mes[0]]()
		elif len(mes) == 2:
			res = types[mes[0]](mes[1])
		elif len(mes) == 3:
			res = types[mes[0]](mes[1], mes[2])
		
		return rtype, len(res), res

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




def main():
	#initialize command socket and start listening
	client_sock = socket.socket()
	client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	client_sock.bind(('', CLIENT_PORT))
	client_sock.listen()
	print("listening in host {} on port {}".format("local", CLIENT_PORT))
	
	ns = NameServer()

	#wait for connection
	while True:
		con, addr = client_sock.accept()
		print(str(addr) + 'connected')
		ns.connect(con)


if __name__ == "__main__":
	main()