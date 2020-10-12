import socket, os
from threading import Thread


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048 


COMMAND_PORT = 3500 #port for commands from name server
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502
FILE_SHARING_PORT = 3503


HOME_DIR = './data'#root directory for dfs files

class Storage(Thread):

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
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def __init__(self, command_sock: socket.socket):
		super().__init__(daemon=True)
		self.command_sock = command_sock


	#connection lost or closed
	def close(self):
		self.command_sock.close()
		print('Client disconected')


	#main thread
	def run(self):
		mess = self.command_sock.recv(BUFFER_SIZE).decode('utf-8')
		rtype, lenght, data = self.parse_and_exec(mess)
		resp = self.make_resp(rtype, str(lenght), data)
		print(resp)
		self.command_sock.send(resp)
		self.close()

	'''
	parse and execute the message
	'''
	def parse_and_exec(self, message):
		#dictionary with all possible functions
		types ={'crf':self.create,
				'cpf':self.copy,
				'mvf':self.move,
				'down':self.download,
				'up':self.upload,
				'inf':self.fsTree,
				'init':self.init,
				'rmf':self.delete,
				'shl':self.share_listen,
				'shu':self.share_upload
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
		elif len(mes) == 5:
			res = types[mes[0]](mes[1], mes[2], mes[3])
		elif len(mes) == 6:
			res = types[mes[0]](mes[1], mes[2], mes[3], mes[4])
		
		return rtype, len(res), res

	'''
	clear all
	'''
	def init(self):
		os.system('rm -rf ' + HOME_DIR + '/')
		os.system('mkdir '+ HOME_DIR)
		stream = os.popen('df -a -h '+ HOME_DIR)
		t = stream.read()
		t = t.split('\n')[1].split(' ')
		t = [i for i in t if i != '']
		avaliable_space = t[3]
		res = ''
		res += avaliable_space
		return res


	''' Create new empty file '''
	def create(self, filename):
		print(filename)
		stream = os.popen("touch '" + HOME_DIR+filename+"'")
		res = stream.read()
		if res == '':
			res == 'Success '
		return res

	''' 
	Download file from Client
	'''
	def download(self, filename, filesize, host, port):
		file_size = int(filesize)

		filename = HOME_DIR + filename

		#caculate number of 2KB chunks in the file
		#and size of remaining data
		n_blocks = file_size//BUFFER_SIZE
		extra_block = file_size - n_blocks*BUFFER_SIZE

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		sock.connect((host, int(port)))

		f = open(filename, 'wb')

		for i in range(n_blocks):
			block = sock.recv(BUFFER_SIZE)
			f.write(block)

		block = sock.recv(extra_block)
		f.write(block)
		sock.close()
		f.close()

		return str(file_size) + ' bytes recieved'

	''' 
	Upload file to Clent
	'''
	def upload(self, name, host, port):
		
		filename = HOME_DIR + name
		
		file_size = os.path.getsize(filename)
		print(filename + ' requested size:' + str(file_size))
		#caculate number of 2KB chunks in the file
		#and size of remaining data
		n_blocks = file_size//BUFFER_SIZE
		extra_block = file_size - n_blocks*BUFFER_SIZE

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		sock.connect((host, int(port)))

		f = open(filename, 'rb')

		for i in range(n_blocks):
			block = f.read(BUFFER_SIZE)
			sock.send(block)

		block = f.read(extra_block)
		sock.send(block)
		sock.close()
		f.close()
		

		return str(file_size) + ' bytes sent'

	''' 
	Delete existing file from DFS
	'''
	def delete(self, filename):
		stream = os.popen('rm ' + HOME_DIR+filename)
		return stream.read()

	'''
	Provide information about the file
	'''
	def info(self, filename):
		stream = os.popen('ls -l ' + HOME_DIR+filename)
		return stream.read()

	'''
	Create a copy of file
	'''
	def copy(self, filename, newpath):
		stream = os.popen('cp '+ HOME_DIR+filename + ' ' + HOME_DIR+newpath)
		return stream.read()

	'''
	Move given file to specified directory
	'''
	def move(self, file, newpath):
		stream = os.popen('mv '+ HOME_DIR+file + ' ' + HOME_DIR+newpath)
		return stream.read()

	'''
	Open directory
	'''
	def opendir(self, dir_path):
		return 'Not yet'

	'''
	List the files in the directory
	'''
	def readdir(self, dir_path):
		return os.listdir(HOME_DIR+dir_path)
	'''
	Create new directory
	'''
	def mkdir(self, dir_path):
		stream = os.popen('mkdir '+ HOME_DIR+dir_path)
		return stream.read()

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	#does not ask, you want - I delete
	def deldir(self, dir_path):
		stream = os.popen('rm -r '+ HOME_DIR+dir_path)
		return stream.read()

	'''
	List all files in the system
	'''
	def fsTree(self):
		stream = os.popen('ls ' + HOME_DIR)
		res = stream.read().replace(' ', '\n')
		return res

	'''
	share file recieve
	'''
	def share_listen(self, filename):
		#create a sharing socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		sock.bind(('', FILE_SHARING_PORT))
		#accept connection from sharing storage
		conn, addr = sock.accept()
		#get filesize and calculate number of blocks
		file_size = int(conn.recv(BUFFER_SIZE).split(SEPARATOR)[0])
		n_blocks = file_size//BUFFER_SIZE
		extra_block = file_size - n_blocks*BUFFER_SIZE

		#create file
		f = open(filename, 'wb')

		#recieve blocks and write them to file
		for i in range(n_blocks):
			block = sock.recv(BUFFER_SIZE)
			f.write(block)
		#get remaning data
		block = sock.recv(extra_block)
		f.write(block)
		sock.close()
		f.close()
		return 'Done'

	'''
	share file upload
	'''
	def share_upload(self, dest, filename):

		file_size = os.path.getsize(filename)
		print(filename + ' requested size:' + str(file_size))
		#caculate number of 2KB chunks in the file
		#and size of remaining data
		n_blocks = file_size//BUFFER_SIZE
		extra_block = file_size - n_blocks*BUFFER_SIZE

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		sock.connect((dest, FILE_SHARING_PORT))

		sock.send(self.make_req(str(file_size)))

		f = open(filename, 'rb')

		for i in range(n_blocks):
			block = f.read(BUFFER_SIZE)
			sock.send(block)

		block = f.read(extra_block)
		sock.send(block)
		sock.close()
		f.close()
		return 'Done'



#listen for roll cals and answer name server's broadcasts
def heart():
	#UDP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	sock.bind(('', DISCOVER_PORT))
	#always listen
	#when recieved send response to broadcast origin 
	while True:
		data, addr = sock.recvfrom(BUFFER_SIZE)
		host, port = addr
		print('Broadcast recieved from ' + host)
		mess = b'Alive'
		resp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		resp_sock.sendto(mess, (host, DISCOVER_RESPONSE_PORT))



def main():
	if not os.path.exists(HOME_DIR):
		os.system('mkdir '+ HOME_DIR)


	#initialize command socket and start listening
	command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	command_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	command_sock.bind(('', COMMAND_PORT))
	command_sock.listen()

	#start a thread that will answer roll calls
	hart = Thread(target = heart, daemon=True)
	hart.start()
	
	#wait for connection
	while True:
		#create Storage class instance in separate thread
		con, addr = command_sock.accept()
		print(str(addr) + 'connected')
		Storage(con).start()


if __name__ == "__main__":
	main()