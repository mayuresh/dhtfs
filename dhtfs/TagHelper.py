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

import md5	
import os
import logging
import stat
from dhtfs.Tagging import Tagging

class TagFile:
	"""
	This class represents a file in dhtfs.

	Objects of this class will be used as Elements and tags will be associated with them.
	The Instances of this class have two propeties 'location' and 'name' which are used
	to identify the instances.
	"""
	def __init__(self, location, name):

		self.location = os.path.normpath(location)
		self.name = name
		self.__hash = (self.location + self.name).__hash__() # Avoid recomputing

	def __hash__(self):
		return self.__hash

	def __repr__(self):
		if self.location:
			return '<location=%s:name=%s>' % (self.location, self.name)

	def __str__(self):
		if self.location:
			return self.name + " at " + self.location

	def __eq__(self, f):
		if f.location == self.location and  f.name == self.name:
			return True
		else:
			return False

	def __nonzero__(self):
		if self.location == None:
			return False
		else:
			return True

class TagDir(Tagging):
	"""
	This class extends Tagging and implements functions which help in mapping tags to directories
	"""

	DEFAULT_DIR_MODE = (stat.S_IRWXO | stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IWRITE)

	def __str__(self):
		return 'Directory helper for ' + Tagging.__str__(self)

	def __createActualDirs(self, dirs, mode):
		allDirs = self.getAllDirs()
		dirs = [x for x in dirs if x not in allDirs]
		for dir in dirs:
			dirname = os.path.join(self.db_path, 't_' + dir)
			if not os.path.isdir(dirname):
				os.mkdir(dirname, mode)

	def __delActualDirs(self, dirs):
		allDirs = self.getAllDirs()
		dirs = [x for x in dirs if x in allDirs]
		for dir in dirs:
			dirname = os.path.join(self.db_path, 't_' + dir)
			if os.path.isdir(dirname):
				os.rmdir(dirname)
	
	def __renameActualDir(self, dir1, dir2):
		actualDirname1 = os.path.join(self.db_path, 't_' + dir1)
		actualDirname2 = os.path.join(self.db_path, 't_' + dir2)
		os.rename(actualDirname1, actualDirname2)
	
	def renameDir(self, dirs1, dirs2):
		"""
		Rename directories
		"""
		
		fileList = Tagging.getElements(self, tagList=dirs1)
		Tagging.delTagsFromElements(self, dirs1, elementList=fileList)
		Tagging.addTags(self, elementList=fileList, newTagList=dirs2)

		if [dirs1[-1] != dirs2[-1]]:
			self.__renameActualDir(dirs1[-1], dirs2[-1])

	def addDirsToFiles(self, fileList, dirList, mode=DEFAULT_DIR_MODE):
		"""
		Associates the specified directories to the specified files

		@param fileList: List of files to be used
		@type fileList: List of instances of L{TagFile}

		@param dirList: List of directories
		@type dirList: List of str

		@param mode: Mode with which the directories are to be created, if required
		@type mode: int
		"""
		self.__createActualDirs(dirList, mode)
		Tagging.addTags(self, fileList, dirList)

	def createDirs(self, dirs, mode=DEFAULT_DIR_MODE):
		"""
		Create Directories

		@param dirs: directories to be created
		@type dirs: List of str

		@param mode: Mode with which the directories are to be created, if required
		@type mode: int
		"""
		self.__createActualDirs(dirs, mode)
		Tagging.addTags(self, newTagList=dirs)

	def delDirs(self, dirs):
		"""
		Delete Directories

		@param dirs: directories to be created
		@type dirs: List of str
		"""
		self.__delActualDirs(dirs)
		Tagging.delTagsFromElements(self, dirs)

	def delFilesFromDirs(self, files, dirs):
		"""
		Delete files from directories

		@param files: List of files to be used
		@type files: List of instances of L{TagFile}

		@param dirs: List of directories
		@type dirs: List of str
		"""

		self.__delActualDirs(dirs)
		Tagging.delTagsFromElements(self, dirs, files)

	def delFiles(self, files, dirs=[]):
		"""
		Delete files

		@param files: List of files to be used
		@type files: List of instances of L{TagFile}
		"""

		Tagging.delElementsFromTags(self, files, tagList=dirs)
		
	def getAllDirs(self):
		"""
		Get a list of all directories

		@return: List of all directories
		@rtype: List of str
		"""

		return Tagging.getTagsForTags(self, tagList = [])

	def getDirsForFiles(self, files):
		"""
		Get directories which contain the given files

		@param files: List of files to be used
		@type files: List of instances of L{TagFile}

		@return: List of all directories
		@rtype: List of str
		"""

		return Tagging.getTagsForElements(self, files)

	def getDirsForDirs(self, dirList):
		"""
		Get directories which contain the files contained in the given directories

		@param dirList: List of directories to be used
		@type dirList: List of str

		@return: List of all directories
		@rtype: List of str
		"""

		return Tagging.getTagsForTags(self, dirList)

	def getDirsAndFilesForDirs(self, dirList, beRestrictive=False, getCover=False):
		"""
		Get files contained in all the directories specified in dirList. Also get list of other directories which contain ANY of these files

		@param dirList: List of directories to be used
		@type dirList: List of str

		@param beRestrictive: Only return those directories which are NOT associated with ALL the files
			with which the given list of directories is associated.

			The philosophy behind this is, having already got a set of files associated
			with the given set of directories, it would be useful to find directories that would restrict
			the set set of directories further. This helps in creating an hierarchy of directories.

			Defaults to False

		@type beRestrictive: bool

		@param getCover: Get a set of directories which between them contain all the files that are contianed
			within the given set of directories.

			This helps particularly when there are large number of tags in the system. Instead of
			looking at 100s of directories it would be helpful to look at only those directories which cover all
			currently selected files.

			Defaults to False

		@type getCover: bool

		@return: A tuple of list of directories and list of files
		@rtype: (List of str, List of instances of L{TagFile})
		"""

		return Tagging.getTagsAndElementsForTags(self, dirList, beRestrictive, getCover)

	def getAllFiles(self):
		"""
		Get a list of all files

		@return: List of all files
		@rtype: List of instances of L{TagFile}
		"""

		return self.getFilesForDirs([])

	def getFilesForDirs(self, dirList):
		"""
		Get a list of files which are contained in all of the given directories

		@param dirList: Directories for which to get files
		@type dirList: List of str

		@return: List of files
		@rtype: List of instances of L{TagFile}
		"""
		return Tagging.getElements(self, dirList)

	def isDir(self, fname):
		"""
		Check whether the specified name is the name of a directory

		@param fname: Name to be checked
		@type fname: str

		@return: True is fname is a directory, False otherwise
		@rtype: bool
		"""
		if fname in self.getAllDirs():
			return True
		else:
			return False

	def getActualLocation(self, dirs, filename):
		filesInDir = Tagging.getElements(self, dirs)
		matchingFiles = [x for x in filesInDir if x.name == filename]
		if len(matchingFiles) == 0:
			return None
		else:
			return matchingFiles[0].location
		
def getLogger(name):
	logging.basicConfig(level=logging.DEBUG,
		format='%(asctime)s: %(levelname)s: %(name)s: %(message)s',
		filename='/tmp/dhtfs.log',
		filemode='a')

	return logging.getLogger(name)

def main():
	from Tagging import Tagging
	import os

	# Set up test environment
	testDirectory = '/tmp/testTagHelper'
	if not os.path.exists(testDirectory):
		os.makedirs(testDirectory)

	files = ['file1', 'file2', 'file3']
	locations = [os.path.join(testDirectory, f) for f in files]

	for l in locations:
		x = file(l, 'w')
		x.write("This is file %s" % l)
		x.close()

	# Create an instance of tagging
	td = TagDir(testDirectory)
	td.initDB(forceInit=True)

	# Save all the files in Tagging DB
	tagFileInstances = []
	for l in locations:
		tf = TagFile(l, os.path.basename(l))
		tagFileInstances.append(tf)

	td.addDirsToFiles(tagFileInstances, ['root'])
	x = td.getFilesForDirs(['root'])
	if len(x) != len(tagFileInstances):
		print 'Test 1 failed'
	else:
		print 'Test 1 passed'

	print x

if __name__ == '__main__':
	main()
