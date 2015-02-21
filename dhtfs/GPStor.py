# Copyright (c) 2006, Mayuresh Phadke
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#         * Redistributions of source code must retain the above copyright
#           notice, this list of conditions and the following disclaimer.
#         * Redistributions in binary form must reproduce the above copyright
#           notice, this list of conditions and the following disclaimer in the
# 	    documentation and/or other materials provided with the distribution.
#         * Neither the name of 'QualEx Systems' nor the names of its
# 	    contributors may be used to endorse or promote products derived from
# 	    this software without specific prior written permission.
# 
#         THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import fcntl
import os
import cPickle

class GPStor:
	"""
	This class implements a persistent store for storing python datatypes.

	Care is taken so that if the store is opened by a process for writing,
	other processes cannot open the store for either reading or writing.
	Many processes may read data from the database simultaneously.

	The data will be stored in a text file in python pickle format.

	Typical usage of this class would be as follows:

	Example 1 
	=========
	from GPStor import GPStor

	gpstor = GPStor('/tmp')
	gpstor.getDataRW()
	gpstor.writeData(['1', '2', '3'])
	print gpstor.getDataRO()

	Example 2
	=========
	from GPStor import GPStor

	gpstor = GPStor('/tmp', 'mydbfile')
	err, l1 = gpstor.getDataRW()
	if err != GPStor.GPS_ERR_SUCCESS:
		print error
		return
	l1.remove('1')
	gpstor.writeData(l1)
	print gpstor.getDataRO()
	"""

	# Error Codes
	GPS_ERR_SUCCESS =	0x00000000 	# Success
	GPS_ERR_NO_LOCK =	0x00000001	# No lock obtained before write
	GPS_ERR_NOSETUP =	0x00000002	# Data store not setup properly
	GPS_ERR_CORRUPT_DB =	0x00000004	# Contents of the data store are corrupted

	# default file for the persistent store
	STORE = '.GPStor_file'

	def checkSetup(cls, db_path=None, db_file=None):
		"""
		GPStor.checkSetup(db_path, db_file) -> True if GPStor files present, otherwise false

		@param db_path:	The path where the database will be stored. This is an advisory path.
				It is not guaranteed that the database will be stored at this path.
				It is guaranteed that if two instances of GPStor are created with same
				db_path argument, they will access the same database.
				Default is to use the path of the current working directory.
		@type db_path: string

		@param db_file: The name of the file to be used for the persistent store.
				A default name will be chosen if not specified.
		@type db_file: string

		@return: True if GPStor files present, otherwise False
		@rtype: C{bool}
		"""

		if not db_path:	
			db_path = os.getcwd()
			
		if not db_file:
			db_file = cls.STORE

		path = os.path.join(db_path, db_file)
		if os.path.isfile(path) and os.path.isfile(path + '.lock'):
			return True
		else:
			return False

	checkSetup = classmethod(checkSetup)


	def __repr__(self):
		return 'Database at %s' % (self.__storeFile)

	def __init__(self, db_path = os.getcwd(), db_file = STORE, caching = True):
		"""
		GPStor() -> instance of GPStor Class

		@param db_path:	The path where the database will be stored. This is an advisory path.
				It is not guaranteed that the database will be stored at this path.
				It is guaranteed that if two instances of GPStor are created with same
				db_path argument, they will access the same database.
				Default is to use the path of the current working directory.
		@type db_path: string

		@param db_file: The name of the file to be used for the persistent store.
				A default name will be chosen if not specified.
		@type db_file: string

		@param caching: Whether caching should be used. Caching will only be used for reads
				Writes will always be written to disk.
		@type caching: boolean
		"""

		# Initialize variables
		self.__db_path = os.path.normpath(db_path)
		self.__storeFile = os.path.join(self.__db_path, db_file)
		self.__lockFile = os.path.join(self.__db_path, db_file + ".lock")

		# Create the store file if not present
		try:
			fd = file(self.__storeFile, 'r')
			fd.close()
		except IOError:
			fd = file(self.__storeFile, 'w')
			fd = file(self.__lockFile, 'w')
			fd.close()
			# If exception is raised here it is passed on to the caller

		self.__lockAcquired = False
		self.__data = None
		self.__lastupdate = 0
		self.__caching = caching

	######## Public functions

	def getDataRO(self):
		"""
		T.getTagDictRO() -> (errorcode, object)

		Get the information stored in Database
		The information got via this function cannot be changed. This function will wait if some other process
		has obtained the database for writing.

		@rtype:	C{(int, object)}
		@return: (errorcode, object)
			1. errorcode = 	L{GPS_ERR_SUCCESS} on success,
					L{GPS_ERR_NOSETUP} if database is not setup
					L{GPS_ERR_CORRUPT_DB} if database is corrupted
			2. object = object stored in the database
		"""

		ret = self.__lockSH() # Acquire a shared lock
		if ret != GPStor.GPS_ERR_SUCCESS:
			return ret, {}

		ret, data = self.__getData()

		self.__unlock() # release the lock

		return (ret, data)

	def getDataRW(self):
		"""
		T.getTagDictRW() -> (errorcode, object)

		Get the information stored in Database
		The information got via this function can be changed. This function will wait if some other process
		has obtained the database for reading or writing.

		@rtype:	C{(int, object)}
		@return: (errorcode, object)
			1. errorcode = 	L{GPS_ERR_SUCCESS} on success,
					L{GPS_ERR_NOSETUP} if database is not setup
					L{GPS_ERR_CORRUPT_DB} if database is corrupted
			2. object = object stored in the database
		"""

		ret = self.__lockEX() # Acquire an exclusive lock
		if ret != GPStor.GPS_ERR_SUCCESS:
			return ret, {}

		self.__lockAcquired = True

		ret, data = self.__getData()

		return (ret, data)

	def writeData(self, data):
		"""
		T.writeData(object) -> store the object to the database

		Store a python object to the database.
		This will overwrite any previous contents of the database

		@param data:	Python object to be stored to Database
		@type data: object

		@return: 
			1. L{GPS_ERR_SUCCESS} on success.
			2. L{GPS_ERR_NOSETUP} if database was not found at the given path
			3. L{GPS_ERR_NO_LOCK} if function was called without acquiring the necesary lock
		"""
		# check whether lock has been acquired
		# Return error if a lock was not acquired
		if not self.__lockAcquired:
			return GPStor.GPS_ERR_NO_LOCK
			
		ret = self.__writeDataToStore(data)
		self.__updateCache(data)

		self.__unlock()
		self.__lockAcquired = False
		return self.GPS_ERR_SUCCESS


	################################### Helper functions

	def __storeExists(self):
		if not os.path.exists(self.__storeFile):
			return False
		
		return True
	
	############### Functions for getting data

	def __getData(self):

		if self.__caching and self.__isCacheUpToDate():
			return GPStor.GPS_ERR_SUCCESS, self.__data

		# Either caching is disabled or the cache is not valid
		# get the data from the persistent store
		ret, data = self.__getDataFromStore()

		if ret == GPStor.GPS_ERR_SUCCESS:
			self.__updateCache(data)
		else:
			self.__invalidateCache()

		return (ret, data)

	def __getDataFromStore(self):
		if not self.__storeExists(): # Store does not exist
			return GPStor.GPS_ERR_NOSETUP, None
			
		f = open(self.__storeFile, "r")
		try:
			data = cPickle.load(f) # Read the pickled data from file and unpickle it
			ret = self.GPS_ERR_SUCCESS
		except (cPickle.UnpicklingError, EOFError):
			data = None
			ret = self.GPS_ERR_CORRUPT_DB
		except:
			# TODO: Remove generic except
			data = None
			ret = self.GPS_ERR_CORRUPT_DB

		f.close()
		return (ret, data)

	def __writeDataToStore(self, data):
		if not self.__storeExists(): # Store does not exist
			self.__invalidateCache()
			return

		# Write data into store
		f = open(self.__storeFile, "w")
		cPickle.dump(data, f) # Marshall the dictionary to XML and store it in a file
		f.close()
		self.__invalidateCache()

	###################### Functions for locking

	# Acquire an exclusive lock.
	def __lockEX(self):
		try:
			self.__lockfd = file(self.__lockFile, 'w')
		except:
			return self.GPS_ERR_CORRUPT_DB

		fcntl.lockf(self.__lockfd, fcntl.LOCK_EX)
		return self.GPS_ERR_SUCCESS

	# Acquire shared lock.
	def __lockSH(self):
		try:
			self.__lockfd = file(self.__lockFile, 'r')
		except:
			return self.GPS_ERR_CORRUPT_DB
			
		fcntl.lockf(self.__lockfd, fcntl.LOCK_SH)
		return self.GPS_ERR_SUCCESS

	# Release the lock
	def __unlock(self):
		fcntl.flock(self.__lockfd, fcntl.LOCK_UN)
		self.__lockfd.close()


	########################## Functions for Caching

	def __updateCache(self, data):
		self.__data = data
		self.__lastupdate = os.stat(self.__storeFile).st_mtime

	def __invalidateCache(self):
		self.__data = None
		self.__lastupdate = 0

	def __isCacheUpToDate(self):
		if self.__lastupdate < os.stat(self.__storeFile).st_mtime:
			return False
		else:
			return True

def test():
	TEST_DIR = '/tmp/zzzzzzzzzzzzz'

	print "Running tests ..."
	# Create a directory for testing
	try:
		for root, dirs, files in os.walk(TEST_DIR, topdown=False):
			for name in files:
				os.remove(os.path.join(root, name))
			for name in dirs:
				os.rmdir(os.path.join(root, name))
		os.rmdir(TEST_DIR)
	except:
		pass

	os.mkdir(TEST_DIR)

	if GPStor.checkSetup(TEST_DIR):
		print "checkSetup Test 1 failed"
	else:
		print "checkSetup Test 1 passed"

	# Test 1
	g = GPStor(TEST_DIR)
	if not GPStor.checkSetup(TEST_DIR):
		print "checkSetup Test 2 failed"
	else:
		print "checkSetup Test 2 passed"

	ret, data = g.getDataRW()
	print ret, data
	data = [1, 2, 3]
	ret = g.writeData(data)
	print ret
	ret, data1 = g.getDataRW()
	print ret, data1
	if ret == 0 and data1 == data:
		print "Test1 succesful"
	else:
		print "Test1 Failed"

	# Test 2
	g1 = GPStor()
	ret, data1 = g1.getDataRO()
	if ret == 0 and data1 == data:
		print "Test2 succesful"
	else:
		print "Test2 Failed"

	# Test 3
	ret = g1.writeData(data)
	if ret == GPStor.GPS_ERR_NO_LOCK:
		print "Test3 succesful"
	else:
		print "Test3 Failed"

	# Test 4
	g = GPStor(db_path='/tmp', db_file='my_db', caching=False)
	ret, data = g.getDataRW()
	data = range(1,10000)
	ret = g.writeData(data)
	print ret
	ret, data1 = g.getDataRW()
	#print ret, data1
	if ret == 0 and data1 == data:
		 print "Test4 succesful"
	else:
		 print "Test4 Failed"

if __name__ == "__main__":
	test()
