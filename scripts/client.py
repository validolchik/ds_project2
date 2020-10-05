'''import time
import request
import os
'''

class Client():

	'''
	Initialize the client storage on a new system
	Remove any existing file in the dfs root dir and return available size 
	'''
	def init():
		pass

	''' Create new empty file '''
	def create():
		# i guess something like touch
		pass

	''' 
	Read file from DFS
	Download it to client host
	'''
	def read():
		pass

	''' 
	Upload file to DFS
	'''
	def write():
		pass

	''' 
	Delete existing file from DFS
	'''
	def delete():
		pass

	'''
	Provide information about the file
	'''
	def info():
		pass

	'''
	Create a copy of file
	'''
	def copy():
		pass

	'''
	Move given file to specified directory
	'''
	def move(file, newpath):
		pass

	'''
	Open directory
	'''
	def opendir(dir_path):
		pass

	'''
	List the files in the directory
	'''
	def readdir(dir_path):
		pass

	'''
	Create new directory
	'''
	def mkdir():
		pass

	'''
	Delete directory
	If any files exists, ask for confirmation
	'''
	def deldir():
		pass
