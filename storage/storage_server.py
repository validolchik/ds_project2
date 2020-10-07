import socket, os, sys
from threading import Thread


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048 


COMMAND_PORT = 3500 #port for commands from name server
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502


HOME_DIR = './data'#root directory for dfs files

class Storage(Thread):

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
		rtype, length, res = self.parse_and_exec(mess)
		print(rtype + ' recieved')
		resp = f'{rtype}][{length}][{res}'
		print(resp)
		self.command_sock.send(resp.encode('utf-8'))
		self.close()

	'''
	parse and execute the message
	'''
	def parse_and_exec(self, message):
		#dictionary with all possible functions
		types ={'crf':self.create,
				'cpf':self.copy,
				'mvf':self.move,
				'rmdir':self.deldir,
				'mkdir':self.mkdir,
				'opdir':self.opendir,
				'down':self.download,
				'up':self.upload,
				'inf':self.fsTree
				}

		#split message and get request type
		mes = message.split(SEPARATOR)
		rtype = mes[0]
		
		res = 0
		#execute function with needed amount of arguments
		if len(mes) == 2:
			res = types[mes[0]]()
		elif len(mes) == 3:
			res = types[mes[0]](mes[1])
		elif len(mes) == 4:
			res = types[mes[0]](mes[1], mes[2])
		
		return rtype, len(res), res

	'''
	clear all
	'''
	def init(self):
		return 'Not yet'


	''' Create new empty file '''
	def create(self, filename):
		stream = os.popen('touch ' + HOME_DIR+filename)
		return stream.read()

	''' 
	Read file from DFS
	Download it to client host
	'''
	def download(self, filename):
		return 'Not yet'

	''' 
	Upload file to DFS
	'''
	def upload(self, filename):
		return 'Not yet'

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
	List all directories and files in the system
	'''
	def fsTree(self):
		stream = os.popen('ls -l -R ' + HOME_DIR + '/')
		out = stream.read().split('\n\n')
		res = ''
		for block in out:
			lines = block.split('\n')
			res += lines[0]+'\n'
			if len(lines) > 3:
				for l in lines[2:]:
					is_directory = l[0]=='d'
					line = [i for i in l.split(' ') if i != '']
					print(line)
					size = line[4]
					name = ''.join(line[8:])
					res += name
					if not is_directory:
						res += ' ' + size
					res += '\n'
			res += '\n'
		return res


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
	if not os.path.exists('./data'):
		os.system('mkdir data')


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