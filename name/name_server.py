import socket, os, sys
from threading import Thread
import time
import json

SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048

CLIENT_PORT = 6235
COMMAND_PORT = 3500
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502#port to listen broadcasts response
HOST = '0.0.0.0'

CATALOG_FILE = 'catalog.txt'#catalog file
CATALOG = {}#dictonary of storages and their file systems

class NameServer():

	'''
	Read an existing catalog file or create a new one
	'''
	def read_catalog(self):
		#if no catalogue file exist create one
		if not os.path.isfile(CATALOG_FILE):
			with open(CATALOG_FILE, 'w') as f:
				json.dump({}, f)
		#then read the file
		with open(CATALOG_FILE) as f:
			self.catalog = json.load(f)

	'''
	Read servers files and
	Update the catalog file
	'''
	def update_catalog(self):
		cat = {}
		command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		for s in self.storages:
			command_sock.connect((s, COMMAND_PORT))
			req = f'inf{SEPARATOR}' 
			pad = BUFFER_SIZE - len(req)
			req += pad*' '
			command_sock.send(req.encode('utf-8'))
			resp = command_sock.recv(6).decode('utf-8')
			while resp[-2] + resp[-1] != SEPARATOR:
				resp += command_sock.recv(1).decode('utf-8')
			print(resp)
			lenght = int(resp.split(SEPARATOR)[1])
			print(lenght)
			resp = command_sock.recv(lenght).decode('utf-8')
			
			cat[s] = resp

		print(cat)

		with open(CATALOG_FILE, 'w') as f:
			json.dump(cat, f)

	'''
	start a storage discovery thread
	'''
	def __init__(self):
		self.curr_dir = '/'
		explorer = Thread(target = self.explorer, daemon=True)
		explorer.start()


	'''
	perform perodic(30sec) storage rediscovery

	might result in having to redo the messages
	'''
	def explorer(self):
		listener = Thread(target = self.listen, daemon=True)
		listener.start()
		self.discover()
		time.sleep(5)
		self.update_catalog()
		while True:
			time.sleep(30)
			self.discover()
			time.sleep(5)
			print(self.storages)
			self.update_catalog()

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
		print('Answer from '+ host)
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


	'''
	assign client socket and start executing commands
	'''
	def connect(self, sock:socket.socket):
		self.client_sock = sock
		self.run()

	#connection lost or closed
	def close(self):
		self.client_sock.close()
		print('Client disconected')
		return 0

	'''
	end communication and close connection
	'''
	def exit(self):
		print('Client want to end connection')
		self.close()
		return 0

	'''
	read messages and exucute corresponding functions
	'''
	def run(self):
		mess = self.client_sock.recv(BUFFER_SIZE).decode('utf-8')
		rtype, lenght, res = self.parse_and_exec(mess)
		while rtype != self.exit:
			resp = f'{rtype}][{length}][{res}'
			self.client_sock.send(resp.encode('utf-8'))
			mess = self.client_sock.recv(BUFFER_SIZE).decode('utf-8')
			rtype, lenght, res = mess.split(SEPARATOR)

		


	'''
	parse and execute the message
	'''
	def parse_and_exec(self, message):
		#dictionary with all possible functions
		types ={'init':self.init,
				'crf':self.create,
				'cpf':self.copy,
				'mvf':self.move,
				'rmdir':self.deldir,
				'mkdir':self.mkdir,
				'opdir':self.opendir,
				'down':self.download,
				'up':self.upload,
				'exit':self.exit
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



	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def init(self):
		return 'Initialized'


	''' Create new empty file '''
	def create(self):
		# i guess something like touch
		return 'Not yet'

	''' 
	Read file from DFS
	Download it to client host
	'''
	def read(self):
		return 'Not yet'

	''' 
	Upload file to DFS
	'''
	def write(self):
		return 'Not yet'

	''' 
	Delete existing file from DFS
	'''
	def delete(self):
		return 'Not yet'

	'''
	Provide information about the file
	'''
	def info(self):
		return 'Not yet'

	'''
	Create a copy of file
	'''
	def copy(self):
		return 'Not yet'

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		return 'Not yet'

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		return 'Not yet'

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		return 'Not yet'

	'''
	Create new directory
	'''
	def mkdir(self):
		return 'Not yet'

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir(self):
		return 'Not yet'




def main():
	#initialize command socket and start listening
	client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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