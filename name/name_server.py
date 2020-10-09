import socket, os
from threading import Thread
import random
import time
import json

SEPARATOR = "][" # separator for filename and size transferring
FILENAME_SEPARATOR = '|'#separates directories to save on storage server
BUFFER_SIZE = 2048

CLIENT_PORT = 6235
COMMAND_PORT = 3500
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502#port to listen broadcasts response
HOST = '0.0.0.0'

FILE_PORT_MIN = 4000
FILE_PORT_MAX = 4100


#Tree for file system catalog
class Tree(object):
	def __init__(self, data, is_dir, parent, info=''):
		self.parent = parent
		self.children = []
		self.is_dir = is_dir
		self.data = data
		self.info = ''

	def add_child(self, node):
		assert isinstance(node, Tree)
		self.children.append(node)



CATALOG_FILE = 'catalog.txt'#catalog file
CATALOG_ROOT = Tree('/', True, None)#file system tree


class NameServer():

	'''
	traverse tree backwards to get full path to the file
	'''
	def get_path(self, node):
		res = ''
		while node.parent != None:
			res = node.parent + FILENAME_SEPARATOR + res
			node = node.parent
		return res

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
	Read servers file structures
	'''
	def get_storage_catalog(self):
		cat = {}
		for s in self.storages:
			self.command_sock.connect((s, COMMAND_PORT))
			req = f'inf{SEPARATOR}' 
			pad = BUFFER_SIZE - len(req)
			req += pad*' '
			self.command_sock.send(req.encode('utf-8'))
			resp = self.command_sock.recv(6).decode('utf-8')
			while resp[-2] + resp[-1] != SEPARATOR:
				resp += self.command_sock.recv(1).decode('utf-8')
			lenght = int(resp.split(SEPARATOR)[1])
			resp = self.command_sock.recv(lenght).decode('utf-8')
			
			cat[s] = resp

		self.storage_catalogs = cat

	'''
	start a storage discovery thread
	'''
	def __init__(self):
		self.curr_dir = CATALOG_ROOT
		self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
		self.get_storage_catalog()
		while True:
			time.sleep(30)
			self.discover()
			time.sleep(5)
			self.get_storage_catalog()

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
		print('Storage '+ host + ' alive')
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

	#close connection with client
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
			rtype, lenght, res = self.parse_and_exec(mess)



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
		
		res = ''
		#execute function with needed amount of arguments
		if len(mes) == 2:
			res = types[mes[0]]()
		elif len(mes) == 3:
			res = types[mes[0]](mes[1])
		elif len(mes) == 4:
			res = types[mes[0]](mes[1], mes[2])
		
		return rtype, len(res), res


	'''
	Get response and extract body
	'''
	def get_response(self, sock, rtype):
		resp = self.command_sock.recv(len(rtype)+len(SEPARATOR)).decode('utf-8')
		while resp[-2] + resp[-1] != SEPARATOR:
			resp += self.command_sock.recv(1).decode('utf-8')
		lenght = int(resp.split(SEPARATOR)[1])
		resp = self.command_sock.recv(lenght).decode('utf-8')
		return resp


	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def init(self):
		CATALOG_ROOT = Tree('/', True, None)
		self.curr_dir = CATALOG_ROOT
		
		res = ''
		for s in self.storages:
			self.command_sock.connect((s, COMMAND_PORT))
			req = f'init{SEPARATOR}' 
			pad = BUFFER_SIZE - len(req)
			req += pad*' '
			self.command_sock.send(req.encode('utf-8'))
			resp = self.get_response(self,command_sock, 'init')
			res += 'storage ' + s + resp + '\n'
		return res


	''' Create new empty file '''
	def create(self, filename):
		res = ''

		#check if file with that name already exists
		already_exists = False
		for c in self.curr_dir.children:
			if c.data == filename:
				already_exists = True

		if not already_exists:
			#add to the tree
			new_file = Tree(filename, False, curr_dir, 'size=0')
			self.curr_dir.add_child(new_file)
			#tell random storage to create a file
			path = self.get_path(new_file)
			path += '][' + filename
			storage = random.choise(self.storages)
			req = 'crf'+SEPARATOR+path+SEPARATOR
			padding = ' '*(BUFFER_SIZE-len(req))
			req += padding
			self.command_sock.connect((s, COMMAND_PORT))
			self.command_sock.send(req)

			#wait for confirmation
			resp = self.get_response(self.command_sock, 'crf')
			res = resp
			if res == '':
				res = 'File craeted'
				new_file.info += '\nreplicas=1'
			else:
				del self.curr_dir.children[-1]
		else:
			res = 'File already exists'

		return res


	''' 
	Read file from DFS
	Download it to client host
	'''
	def read(self):
		#give client a port
		#wait for confirmation
		#tell storage filesize and name
		#tell storage to connect to client
		return 'Not yet'

	''' 
	Upload file to DFS
	'''
	def write(self):
		#give client a port
		#wait for confirmation
		#tell storage filesize and name
		#tell storage to connect to client
		return 'Not yet'

	''' 
	Delete existing file from DFS
	'''
	def delete(self, filename):
		res = ''
		el = None

		#find a file with given name
		for i in range(len(self.curr_dir.children)):
			if self.curr_dir.children[i].data == filename and not self.curr_dir.children[i].is_dir:
				el = i


		if el == None:
			res = 'No such file'
		else:
			del self.curr_dir.children[el]
			res = 'Done'
		return res

	'''
	Provide information about the file
	'''
	def info(self, filename):
		res = ''

		#check if file with that name already exists
		file = None
		for c in self.curr_dir.children:
			if c.data == filename:
				file = c

		if file == None:
			res = 'No such file exist'
		else:
			res = file.info

		return res

	'''
	Create a copy of file
	'''
	def copy(self, filename, newpath):
		res = ''

		#check if file with that name exists
		file = None
		index = 0
		for i in range(len(self.curr_dir.children)):
			c = self.curr_dir.children[i]
			if c.data == filename:
				file = c
				index = 0

		if file == None:
			res = 'No such file exist'
		else:
			#move the file
			new_file = file.deep_copy()
			#del self.curr_dir.children[index]

			newname = filename
			if newpath[-1] != '/':
				newname = newpath.split('/')[-1]
				newpath = ''.join(newpath.split('/')[:-1])
			path = newpath.split('/')
			d = self.curr_dir
			#traverse to requested directory
			try:			
				for p in path:
					if p == '..':
						d = d.parent
					elif p != '':
						for dr in d.children:
							if dr.data == p and dr.is_dir:
								d = dr

				#check if file with such name already exists
				collision = None
				for c in self.curr_dir.children:
					if c.data == newname:
						collision = c
				copy = 1

				#if collision detected add a number at the end
				while collision != None:
					newname = f"{newname.split('.')[0]}({copy}).{newname.split('.')[1]}"
					collision = None
					for c in self.curr_dir.children:
						if c.data == newname:
							collision = c

				#add file to traversed directory
				new_file.data = newname
				new_file.parent = d
				d.add_child(new_file)
				res = 'Done'
			except:
				res = 'Error'

		return res

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		res = ''

		#check if file with that name exists
		file = None
		index = 0
		for i in range(len(self.curr_dir.children)):
			c = self.curr_dir.children[i]
			if c.data == filename:
				file = c
				index = 0

		if file == None:
			res = 'No such file exist'
		else:
			#move the file
			new_file = file.deep_copy()
			del self.curr_dir.children[index]

			newname = filename
			if newpath[-1] != '/':
				newname = newpath.split('/')[-1]
				newpath = ''.join(newpath.split('/')[:-1])
			path = newpath.split('/')
			d = self.curr_dir
			#traverse to requested directory
			try:			
				for p in path:
					if p == '..':
						d = d.parent
					elif p != '':
						for dr in d.children:
							if dr.data == p and dr.is_dir:
								d = dr

				#check if file with such name already exists
				collision = None
				for c in self.curr_dir.children:
					if c.data == newname:
						collision = c
				copy = 1

				#if collision detected add a number at the end
				while collision != None:
					newname = f"{newname.split('.')[0]}({copy}).{newname.split('.')[1]}"
					collision = None
					for c in self.curr_dir.children:
						if c.data == newname:
							collision = c

				#add file to traversed directory
				new_file.data = newname
				new_file.parent = d
				d.add_child(new_file)
				res = 'Done'
			except:
				res = 'Error'

		return res

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		res = ''
		if dir_path == '..':
			if self.curr_dir != CATALOG_ROOT:
				self.curr_dir = self.curr_dir.parent
				res = 'Done'
			else:
				res = 'No such directory'
		else:
			for c in self.curr_dir.children:
				if c.data == dir_path and c.is_dir:
					self.curr_dir = c
					res = 'Done'
			if res != 'Done':
				res = 'No such directory'
		return res

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		res = [[d.data, d.is_dir] for d in self.curr_dir.children]
		for i in range(len(res)):
			if res[i][1]:
				res[i] = res[i][0]+'/\n'
			else:
				res[i] = res[i][0]+'\n'
		return ''.join(res)
		

	'''
	Create new directory
	'''
	def mkdir(self, dirname):
		self.curr_dir.add_child(Tree(dirname, True, self.curr_dir))
		return 'done'

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir(self, dirname):
		res = ''
		el = None

		#find a directory with given name
		for i in range(len(self.curr_dir.children)):
			if self.curr_dir.children[i].data == filename and self.curr_dir.children[i].is_dir:
				el = i


		if el == None:
			res = 'No such directory'
		elif len(self.curr_dir.children[el].children) != 0:
			res = 'Directory is not empty'
		else:
			del self.curr_dir.children[el]
			res = 'Done'
		return res


	'''
	Return representation of the file system
	'''
	def tree(self):
		return 'not yet'





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