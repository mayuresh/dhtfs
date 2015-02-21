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

from dhtfs.GPStor import GPStor
import os

class Tagging:
	"""
	Class for implementing basic tagging operations

	The dictionary maintains mapping from tags to elements as well as elements to tags

	The class uses persistent store provided by L{GPStor}

	The format of the tag dictionary is as follows ::
		dict = { 
			'e2t' :	{
					'element1': ['tag1', 'tag2', ...],
					'element2': ['tag3', 'tag2', ...],
					'element3': ['tag1', 'tag4', ...]
				},
			't2e' :	{
					'tag1': ['element1', 'element2', 'element3', ...],
					'tag4': ['element8', 'element3', 'element3', ...],
					'tag7': ['element9', 'element5', 'element3', ...]
				},
		}
	"""

	DB_FILE = '.tag.db'

	def checkSetup(cls, db_path=None, db_file=None):
		"""
		Check if Tagging is setup in the given directory

		@param db_path:	The path where the Tagging setup is expected.
				Default is to use the path of the current working directory.
		@type db_path: string

		@param db_file: The name of the file which is used to store the Tagging database
				Defaults to L{Tagging.DB_FILE}
		@type db_file: string

		@rtype: C{bool}
		@return: True if Tagging is setup properly, False otherwise.
		"""

		if not db_path:
			db_path = os.getcwd()

		if not db_file:
			db_file = cls.DB_FILE

		return GPStor.checkSetup(db_path=db_path, db_file=db_file)
	
	checkSetup = classmethod(checkSetup)

	def __str__(self):
		return 'Tagging API with %s' % str(self.tagDB)

	def __repr__(self):
		return 'Tagging API with %s' % str(self.tagDB)
		
	# Constructor
	def __init__(self, db_path=os.getcwd(), db_file=DB_FILE, logger=None):
		"""
		Tagging() -> object of class Tagging

		@param db_path: Path to database. Defaults to empty string
		@type db_path: string
		"""

		self.db_path = db_path
		self.db_file = db_file

		if GPStor.checkSetup(db_path=self.db_path, db_file=self.db_file):
			self.tagDB = GPStor(db_path=self.db_path, db_file=self.db_file)
		else:
			self.tagDB = None

		self.useWriteCache = False
		self.tagDict = {}
		self.logger = logger

	##### Helper functions
	
	def __removeValueFromTag(self, tag):
		return tag.split(':')[0]

	def __isValueTag(self, tag):
		if tag.find(':') < 0: return False
		else:	return True

	def __convertToTuple(self, valueTag):
		(tag, value) = valueTag.split(':', 1)
		return (tag, value)

	##### Functions for implementing write cache
	
	def __getTagDictRW(self):
		if self.useWriteCache:
			return 0, self.tagDict
		else:
			return self.tagDB.getDataRW()
	
	def __writeTagDict(self, tagDict):
		if self.useWriteCache:
			self.tagDict = tagDict
		else:
			self.tagDB.writeData(tagDict)

	def setWriteCaching(self):
		self.useWriteCache = True
		err, self.tagDict = self.tagDB.getDataRW()

	def doneWriteCaching(self):
		self.useWriteCache = False	
		self.tagDB.writeData(self.tagDict)

	##### Book keeping operations

	# Initialize the database
	def initDB(self, forceInit=False):
		"""
		T.initGPStor(forceInit) -> Initialize the database with default values

		@param forceInit: Initialize even if database exists
		@type forceInit: boolean
		"""
		if GPStor.checkSetup(db_path=self.db_path, db_file=self.db_file) and not forceInit:
			return

		self.tagDB = GPStor(db_path=self.db_path, db_file=self.db_file)
		self.tagDB.getDataRW()
		self.tagDB.writeData({ 'e2t' : {}, 't2e' : {}, 'e2a' : {} })

	###### Add, Delete, Rename tags

	# Add tags to the DB
	def addTags(self, elementList = [], newTagList = []):
		"""
		T.addTags(elementList, newTagList) -> Associate all the tags in the tagList with all the elements in the element list

		@param elementList: List of elements to associate tags to. Defaults to an empty list
		@type elementList: List

		@param newTagList: List of tags to associate with the elements. Defaults to an empty list
		@type newTagList: List
		"""

		if len(elementList) == 0 and len(newTagList) == 0:
			return

		err, tagDict = self.__getTagDictRW()
		if err != 0:
			return
		
		# Remove blank tags
		newTagList = [x for x in newTagList if x != '']

		# Create element to tag mapping
		for element in elementList:
			try:
				tagDict['e2t'][element].update(newTagList)
			except KeyError:
				tagDict['e2t'][element] = set(newTagList)

		# Create tag to element mapping
		# Do not store the value part of the tag in the tag to element mapping

		for tag in newTagList:
			try:
				tagDict['t2e'][tag].update(elementList)
			except KeyError:
				tagDict['t2e'][tag] = set(elementList)

		self.__writeTagDict(tagDict)
	
	# delete Elements
	def delElementsFromTags(self, elementList, tagList = []):
		"""
		T.delElementsFromTags(tagList, elementList) -> delete all the elements in the element list, from all tags in the tagList

		@param elementList: List of elements to delete tags from.
		@type elementList: List

		@param tagList: List of tags to delete from elements. Defaults to an empty list. Empty list means all tags.
		@type tagList: List
		"""

		err, tagDict = self.__getTagDictRW()
		if err != 0:
			return

		if len(tagList) == 0:
			for tag in tagDict['t2e'].keys():
				tagDict['t2e'][tag].difference_update(elementList)

			for element in elementList:
				try:
					del tagDict['e2t'][element]
				except KeyError:
					pass
		else:
			for tag in tagList:
				try:
					tagDict['t2e'][tag].difference_update(elementList)
				except KeyError:
					pass

			for element in elementList:
				try:
					tagDict['e2t'][element].difference_update(tagList)
					if len(tagDict['e2t'][element]) == 0:
						del tagDict['e2t'][element]
				except KeyError:
					pass

		self.__writeTagDict(tagDict)
	
	# delete tags from the DB
	def delTagsFromElements(self, tagList, elementList = []):
		"""
		T.delTagsFromElements(tagList, elementList) -> delete all the tags in the tagList from all the elements in the element list

		@param elementList: List of elements to delete tags from. Defaults to an empty list. Empty list deletes tags from all elements
		@type elementList: List

		@param tagList: List of tags to delete from elements.
		@type tagList: List
		"""
		err, tagDict = self.__getTagDictRW()
		if err != 0:
			return
		
		if len(elementList) == 0:
			for element in tagDict['e2t'].keys():
				tagDict['e2t'][element].difference_update(tagList)

			for tag in tagList:
				try:
					del tagDict['t2e'][tag]
				except KeyError:
					pass
		else:
			for element in elementList:
				try:
					tagDict['e2t'][element].difference_update(tagList)
				except KeyError:
					pass

			for tag in tagList:
				try:
					tagDict['t2e'][tag].difference_update(elementList)
					if len(tagDict['t2e'][tag]) == 0:
						del tagDict['t2e'][tag]
				except KeyError:
					pass

		self.__writeTagDict(tagDict)
	
	def renameTag(self, oldTagName, newTagName):
		"""
		T.renameTag(oldTagName, newTagName) -> rename a tag. Tag all the elements that were tagged with the old tag with newTagName

		@param oldTagName: Old tag name
		@type oldTagName: string

		@param newTagName: Old tag name
		@type newTagName: string
		"""

		elementList = self.getElements(tagList=[oldTagName])

		self.delTagsFromElements(elementList=[], tagList=[oldTagName])
		self.addTags(elementList, [newTagName])

	####### Get tagging information

	# Get a python dictionary which contains list of tags for each element
	def getTagsDict(self):
		"""
		T.getTagsDict() -> Get a python dictionary which maps elements to tags

		The format of the dictionary is ::

			{ 'element1' : ['tag1', 'tag2', 'tag3' ...],
			  'element2' : [ ...],
			  ...
			}

		@return: Dictionary of element to tag mapping
		@rtype: C{dict}
		"""
		
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return {}

		return tagDict['e2t'].copy()
			
	# Get a python dictionary which contains list of elements for each tag
	def getElementsDict(self):
		"""
		T.getElementsDict() -> Get a python dictionary which maps tags to elements

		The format of the dictionary is ::

			{ 'tag1' : ['element1', 'element2', 'element3' ...],
			  'tag2' : [ ...],
			  ...
			}

		@return: Dictionary of element to tag mapping
		@rtype: C{dict}
		"""
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return {}

		return tagDict['t2e'].copy()

	# Get all the tags associated with the given elements
	def getTagsForElements(self, elementList=[], filterList=[], filter=None):
		"""
		T.getTags() -> Get list of all tags associated with the given list of elements

		@param elementList: List of elements for which the tags are to be fetched. If an empty
					list is supplied get all the tags in the system.
		@type elementList: List

		@param filterList: List of elements to be used for filtering
		@type filterList: List

		@param filter: It can be either "in" which would only return tags that are present in the filterList
			or "not_in" which would only return tags that are NOT present in the filterList
		@type filter: str

		@return: List of tags
		@rtype: C{list}
		"""
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return []

		if len(elementList) == 0:
			return tagDict['t2e'].keys()

		# Each element is associated with a list of tags
		# Get an union of all the tags associated with the elements
		# in the list
		#
		# Do not use the value part of the tag
		#
		# s1.update Updates a set with the union of itself and another
		s1 = tagDict['e2t'].get(elementList[0], set([])).copy()

		for element in elementList[1:]:
			try:
				s1.update(tagDict['e2t'][element])
			except KeyError:
				pass

		if filter == 'in':
			s1.intersection_update(filterList)
		elif filter == 'not_in':
			s1.difference_update(filterList)

		# Convert the set to list
		l = list(s1)
		return l

	def getTagsForTags(self, tagList=[], beRestrictive=False, getCover=False):
		"""
		T.getTagsForTags() -> Get a list of tags associated with the given tags

		Tags associated with the tags is a set of tags with which the associated Elements are tagged.

		@param tagList: List of tags for which the associated Tags are to be fetched.
			Defaults to all the tags in this tagging instance
		@type tagList: List

		@param beRestrictive: Only return those tags which are not associated with all the elements
			with which the given set of tags is associated.

			The philosophy behind this is, having already got a set of elements associated
			with the given set of tags, it would be useful to find tags that would restrict
			the set set of elements further.

			Defaults to False

		@type beRestrictive: bool

		@param getCover: Get a set of tags which between them cover all the elements that are associated
			with the given tags.

			This helps particularly when there are large number of tags in the system. Instead of
			looking at 100s of tags it would be helpful to look at only those tags which cover all
			currently selected elements.

			Defaults to False

		@type getCover: bool

		@return: List of Tags
		@rtype: C{list}
		"""
	
		retTagList, e = self.getTagsAndElementsForTags(tagList, beRestrictive, getCover)	
		return retTagList
	
	def getTagsAndElementsForTags(self, tagList=[], beRestrictive=False, getCover=False):
		"""
		T.getTagsAndElementsForTags() -> Get a list of tags and elements associated with the given tags

		Elements associated with the tags are those which are tagged with all the tags in tagList.
		Tags associated with the tags is a set of tags with which the associated Elements are tagged.

		@param tagList: List of tags for which the associated Elements and Tags are to be fetched.
			Defaults to all the tags in this tagging instance
		@type tagList: List

		@param beRestrictive: Only return those tags which are not associated with all the elements
			with which the given set of tags is associated.

			The philosophy behind this is, having already got a set of elements associated
			with the given set of tags, it would be useful to find tags that would restrict
			the set set of elements further.

			Defaults to False

		@type beRestrictive: bool

		@param getCover: Get a set of tags which between them cover all the elements that are associated
			with the given tags.

			This helps particularly when there are large number of tags in the system. Instead of
			looking at 100s of tags it would be helpful to look at only those tags which cover all
			currently selected elements.

			Defaults to False

		@type getCover: bool

		@return: Tuple (List of Tags, List of Elements)
		@rtype: C{(List, List)}
		"""

		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return [], []

		if len(tagList) == 0:
			retTagList = tagDict['t2e'].keys()
			intersection_set = set(tagDict['e2t'].keys())
		else:
			intersection_set = tagDict['t2e'].get(tagList[0], set([])).copy()

			for tag in tagList[1:]:
				try:
					intersection_set.intersection_update(tagDict['t2e'][tag])
				except KeyError:
					intersection_set.clear()

			retTagSet = set([])
			for e in intersection_set:
				retTagSet.update(tagDict['e2t'][e])
				
			retTagSet.difference_update(tagList)
			retTagList = list(retTagSet)

		if beRestrictive:
			if len(tagList) != 0:
				intersection_set_len = len(intersection_set)
				retTagList = [x for x in retTagList
						if len(tagDict['t2e'][x] & intersection_set) < intersection_set_len]
		elif getCover:
			l = retTagList
			l.sort(key = lambda x: len(tagDict['t2e'][x]), reverse = True)
			cover = []
			while len(l) > 1:
				biggestSet = l[0]
				otherSets = l[1:]
				l = [x for x in otherSets if not tagDict['t2e'][biggestSet] > tagDict['t2e'][x]]
				cover.append(biggestSet)

			retTagList = cover + l

		remainingElements = intersection_set

		if (getCover or beRestrictive) and len(remainingElements) > 20:
			for tag in retTagList:
				remainingElements.difference_update(tagDict['t2e'][tag])

		return retTagList, list(remainingElements)
		
	# Get tags associated with all the elements
	def getCommonTags(self, elementList=[]):
		"""
		T.getCommonTags() -> Get tags which are associated with all the given elements

		@param elementList: List of elements for which to find common tags.
		@type elementList: List

		@return: List of Tags associated with all the elements.
		@rtype: C{list}
		"""
		if len(elementList) == 0:
			return []
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return []

		s1 = tagDict['e2t'].get(elementList[0], set([])).copy()

		for element in elementList[1:]:
			try:
				s1.intersection_update(tagDict['e2t'][element])
			except KeyError:
				s1.clear()
				break

		return list(s1)

	# get frequency of the specified tag
	def getTagsFrequency(self, tagList = [], sortOrder=None):
		"""
		T.getTagsFrequecy() -> Get list of tuples of the form (tag, frequency) for the specified tags

		@param tagList: List of tags for which the frequency is to be fetched.
		@type tagList: List

		@param sortOrder: Can either be "Ascending" to sort in Ascending order, or any other string to
			sort in Descending order
		@type sortOrder: str

		@return: List of Tuples of the form (tag, frequency)
		@rtype: C{list}
		"""
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return []

		if len(tagList) == 0:
			return [(None, 0)]

		retList = []
		for tag in tagList:
			freq = len(tagDict['t2e'].get(tag, []))
			retList.append((tag, freq))

		if sortOrder:
			retList.sort(key = lambda x: x[1], reverse = (sortOrder == 'Ascending'))
			
		return retList

	def getElements(self, tagList=[], elementList=[]):
		"""
		T.getElements(tagList, elementList) -> Get a subset of elements from elementList such that the elements are tagged with tags from tagList

		@param elementList: List of elements. Defaults to empty list
		@type elementList: List

		@param tagList: List of tags. Defaults to empty list
		@type tagList: List

		@return: List of elements. If both elementList and tagList are empty return all elements.
		@rtype: C{list}
		"""

		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return []

		if len(tagList) == 0:
			if len(elementList) > 0:
				return elementList
			else:
				return tagDict['e2t'].keys()

		# Initialize a set with list of elements
		s1 = tagDict['t2e'].get(tagList[0], set([])).copy()
		try:

			# For each tag in the tag list, get elements asociated with the tag
			# the existing set of elements will be intersected with elements associated
			# with the current tag
			for tag in tagList[1:]:
				s1.intersection_update(tagDict['t2e'][tag])

			if len(elementList) > 0:
				s1.intersection_update(set(elementList))

		except KeyError:
			s1.clear()

		# s1 now contains those elements which are associated with all the tags
		# in the tag list

		# Convert the set to list
		l = list(s1)
		return l

	def elementExists(self, element):
		"""
		T.elementExists() -> Checks whether a given element exists in this Tagging instance

		@param element: Element to be checked
		@type element: Object

		@return: True is element exists, False otherwise
		@rtype: C{bool}
		"""
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return ""
			
		if element in tagDict['e2t'].keys():
			return True
		else:
			return False

	def tagExists(self, tag):
		"""
		T.tagExists() -> Checks whether a given tag exists in this Tagging instance

		@param tag: Tag to be checked
		@type tag: str

		@return: True if Tag exists, False otherwise
		@rtype: C{bool}
		"""
		err, tagDict = self.tagDB.getDataRO()
		if err != 0:
			return ""
			
		if tag in tagDict['t2e'].keys():
			return True
		else:
			return False

def main():
		tagging = Tagging("/tmp")
		tagging.initDB(forceInit=True)
		tagging.addTags(['1.txt'], ['work', 'text'])
		tagging.addTags(['1.jpg'], ['work', 'pics'])
		tagging.addTags(['ele1', 'ele2'])
		print tagging.getElements()
		print tagging.getElements(['work'])
		print tagging.getElements(['work'], ['1.txt'])
		print tagging.getElements(['text'])
		print tagging.getElements(['pics'])
		print tagging.getTagsForElements(['1.txt'])
		print tagging.getTagsForElements(['1.jpg'])
		print tagging.getTagsForElements(['1.txt', '1.jpg'])
		tagging.delTagsFromElements(['1.txt'], ['work'])
		print tagging.getTagsForElements(['1.txt'])
		tagging.renameTag('pics', 'pictures')
		print tagging.getElements(['pics'])
		print tagging.getElements(['pictures'])
		print tagging.getTagsForElements(['1.txt'])

# TEST
if __name__ == "__main__":
	main()
