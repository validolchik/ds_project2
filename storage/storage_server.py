import socket, os, sys
from threading import Thread


SEPARATOR = "][" # separator for filename and size transferring
BUFFER_SIZE = 2048 


COMMAND_PORT = 3500 #port for commands from name server
DISCOVER_PORT = 3501
DISCOVER_RESPONSE_PORT = 3502

class Storage(Thread):

	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def __init__(self, command_sock: socket.socket):
		super().__init__(daemon=True)
		self.command_sock = command_sock
		self.current_dir = '/var/data/'#to avoid using cd


	#connection lost or closed
	def close(self):
		self.command_sock.close()
		print('Client disconected')


	#main thread
	def run(self):
		mess = self.command_sock.recv(BUFFER_SIZE).decode('utf-8')
		rtype, length, res = self.parse(mess)
		resp = f'{rtype}][{length}][{res}'
		self.command_sock.send(resp.encode('utf-8'))
		self.close()

	'''
	parse and execute the message
	'''
	def parse(self, message):
		types ={'crf':self.create,
				'cpf':self.copy,
				'mvf':self.move,
				'rmdir':self.deldir,
				'mkdir':self.mkdir,
				'opdir':self.opendir,
				'down':self.download,
				'up':self.upload
				}
		mes = message.split('][')
		rtype = mes[0]
		res = 0
		if len(mes) == 1:
			res = types[mes[0]]()
		elif len(mes) == 2:
			res = types[mes[0]](mes[1])
		elif len(mes) == 3:
			res = types[mes[0]](mes[1], mes[2])
		lenght = len(res)
		return rtype, lenght, res

	''' Create new empty file '''
	def create(self, filename):
		stream = os.popen('touch ' + self.current_dir+filename)
		return stream.read()

	''' 
	Read file from DFS
	Download it to client host
	'''
	def download(self, filename):
		return 0

	''' 
	Upload file to DFS
	'''
	def upload(self, filename):
		return 0

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
		return os.listdir(self.current_dir+dir_path)
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
		return 0



def heart():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	sock.bind(('', DISCOVER_PORT))
	#sock.listen()
	while True:
		data, addr = sock.recvfrom(BUFFER_SIZE)
		host, port = addr
		mess = b'Alive'
		resp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		resp_sock.sendto(mess, (host, DISCOVER_RESPONSE_PORT))



def main():
	#initialize command socket and start listening
	command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	command_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	command_sock.bind(('', COMMAND_PORT))
	command_sock.listen()

	#start a thread that will answer roll calls
	hart = Thread(target = heart)
	hart.start()
	
	#wait for connection
	while True:
		con, addr = command_sock.accept()
		print(str(addr) + 'connected')
		Storage(con).start()


if __name__ == "__main__":
	main()