import socket, os
from threading import Thread
import random
import time

SEPARATOR = "][" # separator for filename and size transferring
FILENAME_SEPARATOR = '|'#separates directories to save on storage server
BUFFER_SIZE = 2048

CLIENT_PORT = 6235
COMMAND_PORT = 3500
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502#port to listen broadcasts response
HOST = '0.0.0.0'#?

FILE_PORTS = [4000,4100]
FILE_SHARE = 3503


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
	build and pad a request with given fields
	'''
	def make_req(self, *args):
		fields = list(args)
		res = ''
		for f in fields:
			res += f + SEPARATOR
		res += ' '*(BUFFER_SIZE-len(res))
		return res.encode('utf-8')

	'''
	build a response
	'''
	def make_resp(self, rtype, lenght, data):
		res = rtype + SEPARATOR + lenght + SEPARATOR + data
		return res.encode('utf-8')

	'''
	traverse tree backwards to get full path to the file
	'''
	def get_path(self, node):
		res = node.data
		while node.parent != None:
			res = node.parent.data + FILENAME_SEPARATOR + res
			node = node.parent
		return res

	'''
	Read an existing catalog file or create a new one
	'''
	def read_catalog(self):
		#if no catalogue file exist create one
		if not os.path.isfile(CATALOG_FILE):
			with open(CATALOG_FILE, 'w') as f:
				f.write(self.tree_to_str())
				f.close()
		#then read the file
		with open(CATALOG_FILE) as f:
			CATALOG_ROOT = self.str_to_tree(f.read())
			f.close()



	'''
	Save current state of FS tree to a file
	'''
	def save_catalog(self):
		with open(CATALOG_FILE, 'w') as f:
			f.write(self.tree_to_str())
			f.close()

	'''
	Read servers file structures
	'''
	def get_storage_catalogs(self):
		self.storage_catalogs = {}
		for s in self.storages:
			req = self.make_req('inf')
			command_sock = socket.create_connection((s, COMMAND_PORT))
			command_sock.send(req)
			resp = self.get_response(command_sock, 'inf')
			command_sock.close()
			resp = resp.split('\n')
			self.storage_catalogs[s] = ['/'+resp[i] for i in range(len(resp)) if resp[i] != '']

	'''
	start a storage discovery thread
	'''
	def __init__(self):
		self.curr_dir = CATALOG_ROOT
		explorer = Thread(target = self.explorer, daemon=True)
		explorer.start()

	'''
	perform perodic(30sec) storage rediscovery
	'''
	def explorer(self):
		listener = Thread(target = self.listen, daemon=True)
		listener.start()
		self.discover()
		time.sleep(1)
		self.get_storage_catalogs()
		while True:
			time.sleep(1)
			self.discover()
			time.sleep(1)
			print(self.storages)
			self.get_storage_catalogs()
			self.sync()

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
	Check which files are not replicated to different storages
	'''
	def sync(self):
		files = [f for f in self.tree_to_str().split('\n') if f != '']
		files = [f.split(SEPARATOR)[0] for f in files if f[-1] != '/']
		# print(self.storage_catalogs)
		# print(files)

		contained = self.storage_catalogs
		missing = {}
		extra = {}

		for s in self.storages:
			#check if storage is missing some files from
			#those that are in the tree
			missing[s] = []
			for file in files:
				if not file in contained[s]:
					missing[s].append(file)

			#check if storage has some additional, unlisted files
			extra[s] = []
			for file in contained[s]:
				if not file in files:
					extra[s].append(file)

		#tell storages to delete extra files
		for s in extra:
			for f in extra[s]:
				req = self.make_req('rmf', f)
				command_sock = socket.create_connection((s, COMMAND_PORT))
				command_sock.send(req)
				resp = self.get_response(command_sock, 'rmf')
				command_sock.close()

		#tell storages to get missing files
		for s in missing:
			for f in missing[s]:
				s2 = ''
				#find a storage that has this file
				for storage in contained:
					if f in contained[storage]:
						s2 = storage
						self.share(s, s2, f)



	'''
	tell storage2 to share a file with storage1
	'''
	def share(self, storage1, storage2, filename):
		#tell storage1 to listen
		req1 = self.make_req('shl', f)
		sock1 = socket.create_connection((storage1, COMMAND_PORT))
		sock1.send(req1)
		#tell storage2 to start sharing
		req2 = self.make_req('shu', storage1, f)
		sock2 = socket.create_connection((storage2, COMMAND_PORT))
		sock2.send(req2)
		#wait for responses
		resp1 = self.get_response(sock1, 'shl')
		sock1.close()
		resp2 = self.get_response(sock2, 'shu')
		sock2.close()
		#done
		print(storage1, 'now have', filename)

	'''
	assign client socket and start executing commands
	'''
	def connect(self, sock:socket.socket, host):
		self.client_sock = sock
		self.client_host = host
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
	main thread
	read messages and give them to parser
	'''
	def run(self):
		mess = self.client_sock.recv(BUFFER_SIZE).decode('utf-8')
		rtype, lenght, res = self.parse_and_exec(mess)
		connected = True
		while connected:
			try:
				resp = self.make_resp(rtype, str(lenght), res)
				print(resp)
				self.client_sock.send(resp)
				mess = self.client_sock.recv(BUFFER_SIZE).decode('utf-8')
				rtype, lenght, res = self.parse_and_exec(mess)
			except:
				connected = False
		self.save_catalog()
		self.close()

	'''
	parse and execute the message
	'''
	def parse_and_exec(self, message):
		#dictionary with all possible functions
		types ={'init':self.init,
				'inf':self.info,
				'crf':self.create,
				'cpf':self.copy,
				'mvf':self.move,
				'rmf':self.delete,
				'rmdir':self.deldir,
				'mkdir':self.mkdir,
				'opdir':self.opendir,
				'rddir':self.readdir,
				'rdf':self.read,
				'wrf':self.write,
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
		resp = sock.recv(len(rtype)+len(SEPARATOR)+1).decode('utf-8')
		while resp[-2] + resp[-1] != SEPARATOR:
			resp += sock.recv(1).decode('utf-8')
		lenght = int(resp.split(SEPARATOR)[1])
		resp = sock.recv(lenght).decode('utf-8')
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
			command_sock = socket.create_connection((s, COMMAND_PORT))
			req = self.make_req('init')
			command_sock.send(req)
			resp = self.get_response(command_sock, 'init')
			command_sock.close()
			res += 'storage ' + s + ' ' +resp + '\n'
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
			new_file = Tree(filename, False, self.curr_dir)
			self.curr_dir.add_child(new_file)
			#tell random storage to create a file
			path = self.get_path(new_file)
			#path += FILENAME_SEPARATOR + filename
			storage = random.choice(self.storages)
			req = self.make_req('crf', path)
			command_sock = socket.create_connection((storage, COMMAND_PORT))
			command_sock.send(req)

			#wait for confirmation
			resp = self.get_response(command_sock, 'crf')
			command_sock.close()
			res = resp
			if res == '':
				res = 'File created'
				new_file.info = 'size=0'+SEPARATOR +'replicas=1'
			else:
				del self.curr_dir.children[-1]
		else:
			res = 'File already exists'

		return res

	''' 
	Read file from DFS
	Upload it to client host
	'''
	def read(self, filename):
		#check if file with such name  exists
		file = None
		for f in self.curr_dir.children:
			if f.data == filename:
				file = f
		if file == None:
			return 'file does not exists'
		#otherwise continue

		#give client a port
		port = random.choice(FILE_PORTS)

		filesize = file.info.split(SEPARATOR)[0][5:]

		data = str(port) + SEPARATOR + str(filesize)
		resp = self.make_resp('rdf', str(len(data)), data)
		print(resp)
		self.client_sock.send(resp)
		#wait for confirmation
		conf = self.client_sock.recv(1).decode()

		#tell random storage to upload a file to the client
		path = self.get_path(file)

		storage = random.choice(self.storages)
		req = self.make_req('up', path, self.client_host, str(port))
		command_sock = socket.create_connection((storage, COMMAND_PORT))
		command_sock.send(req)


		#wait for confirmation
		resp = self.get_response(command_sock, 'up')
		command_sock.close()

		return resp

	''' 
	Upload file to DFS
	'''
	def write(self, filename, filesize):

		#check if file with such name already exists
		file = None
		for f in self.curr_dir.children:
			if f.data == filename:
				file = f
		if file != None:
			return 'file already exists'
		#otherwise continue

		#give client a port
		port = random.choice(FILE_PORTS)

		self.client_sock.send(str(port).encode('utf-8'))
		#wait for confirmation
		conf = self.client_sock.recv(1).decode()

		#tell random storage to download a file from the client
		storage = random.choice(self.storages)
		file = Tree(filename, False, self.curr_dir)
		file.info = 'size='+filesize
		self.curr_dir.add_child(file)
		path = self.get_path(file)
		req = self.make_req('down', path, filesize, self.client_host, str(port))
		command_sock = socket.create_connection((storage, COMMAND_PORT))
		command_sock.send(req)

		#wait for confirmation
		resp = self.get_response(command_sock, 'down')
		command_sock.close()
		
		return resp

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
			path = self.get_path(self.curr_dir.children[el])
			#tell all storages to delete the file
			# for s in self.sorages:
			# 	storage = s
			# 	req = self.make_req('rmf', path)
			# 	command_sock = socket.create_connection((storage, COMMAND_PORT))
			# 	command_sock.send(req)
			# 	resp = self.get_response(command_sock, 'rmf')
			# 	command_sock.close()
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
			res = file.info.replace(SEPARATOR, ' ')

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
			new_file = file.copy()
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
	def move(self, filename, newpath):
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
			new_file = file.copy()
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
	def readdir(self):
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
			if self.curr_dir.children[i].data == dirname and self.curr_dir.children[i].is_dir:
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
	Depth first search
	return all leave nodes
	'''
	def dfs(self, node):
		leaves = []
		for c in node.children:
			if len(c.children) == 0:
				leaves.append(c)
			else:
				leaves += self.dfs(c)
		return leaves


	'''
	String representation of the catalog
	'''
	def tree_to_str(self):
		leaves = self.dfs(CATALOG_ROOT)
		res = ''
		for l in leaves:
			res += self.get_path(l)
			if l.is_dir:
				res += '/'
			else:
				res += SEPARATOR + l.info
			res += '\n'
		return res



	'''
	Parse string representation into a tree
	'''
	def str_to_tree(self, s):
		root = Tree('/', True, None)
		lines = s.split('\n')
		lines = [l.split(FILENAME_SEPARATOR) for l in lines]
		for l in lines:
			if len(l)>1:
				curr_dir = root
				for node in l:
					new_child = None
					if node == l[-1]:
						is_dir = node[-1]=='/'
						if is_dir:
							new_child = Tree(node[:-1], True, curr_dir)
						else:
							info = node.split(SEPARATOR)[-1]
							new_child = (Tree(node, False, curr_dir, info))
					else:
						new_child = (Tree(node, True, curr_dir))
					curr_dir.add_child(new_child)
					curr_dir = new_child

		return root








def main():
	#initialize client socket and start listening
	client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	client_sock.bind(('', CLIENT_PORT))
	client_sock.listen()
	print("listening in host {} on port {}".format("local", CLIENT_PORT))
	
	ns = NameServer()
	ns.read_catalog()

	#wait for connection
	while True:
		con, addr = client_sock.accept()
		host, port = addr
		print(str(addr) + 'connected')
		ns.connect(con, host)


if __name__ == "__main__":
	main()