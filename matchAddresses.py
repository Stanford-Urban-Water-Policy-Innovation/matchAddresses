'''
This script takes two datasets with address variables, cleans and standardizes the address variables
and attempts to perform a match between each set of data. It outputs a matched dataset with the observations
that have been matched (the user can choose to perform an inner, left, right, or outer merge in the process)
The user can also specify variables to check to flag matches that might not be completely accurate.

'''

import pandas as pd 
import numpy as np
import os
import re
import jellyfish


class matchAddresses:

	def __init__(
		self,
		inDir1, inDSN1, keepVars1,
		addressVarsList1, addressVarsTypeList1,
		inDir2, inDSN2, keepVars2,
		addressVarsList2, addressVarsTypeList2	
	):

		# Input arguments for dataset 1
		self.inDir1 = inDir1
		self.inDSN1 = inDSN1
		self.keepVars1 = keepVars1
		self.addressVarsList1 = addressVarsList1
		self.addressVarsTypeList1 = addressVarsTypeList1
		# Input arguments for dataset 2
		self.inDir2 = inDir2
		self.inDSN2 = inDSN2
		self.keepVars2 = keepVars2
		self.addressVarsList2 = addressVarsList2
		self.addressVarsTypeList2 = addressVarsTypeList2

		# Street types and their abbreviations
		os.chdir('/Users/josebolorinos/Google Drive (jbolorin@stanford.edu)/EVP Private/Data/Yelp Data')
		streetTypeSuffixes = pd.read_csv('StreetSuffixAbbreviations.csv')
		self.streetTypesLong = list(streetTypeSuffixes['long'].values)
		self.streetTypesMedium = list(streetTypeSuffixes['medium'].values)
		self.streetTypesAbbrev = list(streetTypeSuffixes['abbrev'].values)

		# Unit types and their abbreviations
		unitTypes = pd.read_csv('UnitAbbreviations.csv')
		self.unitTypesLong = list(unitTypes['long'].values)
		self.unitTypesAbbrev = list(unitTypes['abbrev'].values)

		# Possible variable types (list)
		self.varTypes = ['name','streetNumber','streetName','streetType','unitType','unitNumber','city','zip']


	def getIndex(self, lst, condition):
		index = [IDX for IDX, elem in enumerate(lst) if condition(elem)]
		if index:
			return index[0]


	def getAbbrev(self, addressString):

		addressStringAbbrev = addressString
		if addressString in self.streetTypesMedium:
			IDX = self.getIndex(self.streetTypesMedium, lambda x: x == addressString)
			addressStringAbbrev = self.streetTypesAbbrev[IDX]
		elif addressString in self.streetTypesLong:
			IDX = self.getIndex(self.streetTypesLong, lambda x: x == addressString)
			addressStringAbbrev = self.streetTypesAbbrev[IDX]
		elif addressString in self.unitTypesLong:
			IDX = self.getIndex(self.unitTypesLong, lambda x: x == addressString)
			addressStringAbbrev = self.unitTypesAbbrev[IDX]
		return addressStringAbbrev


	def cleanAddressString(self, addressString):

		# Only keep alphanumeric characters, spaces, and #
		patternChar = re.compile('[^a-zA-Z0-9 #]')
		addressString = patternChar.sub('', addressString)
		# Convert everything to upper case
		addressString = addressString.upper()
		# If the string is a street or unit type, convert to its abbreviation
		addressString = self.getAbbrev(addressString)

		return addressString


	def parseStreetAddress(self, streetAddressStr, strType = None):

		# For counting numbers in alphanumeric string
		patternAlpha = re.compile('[a-zA-Z]')
		# Clean address string
		streetAddressStr = self.cleanAddressString(streetAddressStr)

		# Directions (for removal!)
		directions = ['N','S','E','W','NORTH','SOUTH','EAST','WEST']

		# Set all parsed output variables to None
		streetNumber, streetName, streetType, unitType, unitNumber = '', '', '', '', ''
		# Initialize hasStreet (has a street number, name and type) and hasUnit (has a unit type and number) to False
		hasStreet, hasUnit, streetIDX, unitIDX = False, False, None, None

		# Split street address string into list of words
		streetAddressItems = [item for item in streetAddressStr.split(' ')]

		# Loop through words in street address string to identify street and unit identifiers
		for IDX,item in enumerate(streetAddressItems):

			# Item is a long or abbreviated street type identifier
			if item in self.streetTypesLong + self.streetTypesMedium + self.streetTypesAbbrev:

				# If long street type, replace with its abbreviation
				streetType = self.getAbbrev(item)
				# We now know there is a street address in this string
				hasStreet = True
				# save index of street type identifier
				streetIDX = IDX

			# Item is a long or abbreviated unit type identifier
			elif item in self.unitTypesLong + self.unitTypesAbbrev:

				# If long unit type, replace with its abbreviation
				unitType = self.getAbbrev(item)
				# We now know there is a unit address in this string
				hasUnit = True
				# save index of street type identifier
				unitIDX = IDX

		# Sometimes street and/or unit identifier is missing, 
		# can only handle these cases by knowing whether the string is SUPPOSED to be for a street or a unit...
		if strType == 'street':
			hasStreet = True
		if strType == 'unit':
			hasUnit = True
			if not unitIDX: 
				unitIDX = len(streetAddressItems)
		if strType == 'both':
			hasStreet, hasUnit = True, True
			if not unitIDX:
				unitIDX = len(streetAddressItems)


		# Loop through again
		for IDX,item in enumerate(streetAddressItems):

			# Ignore if it is the street or unit identifier (have already parsed)
			if IDX != streetIDX and IDX != unitIDX:

				# String only contains street address
				if hasStreet and not hasUnit:

					# If the first item is or has a number, probably a street number
					if IDX == 0 and len(patternAlpha.sub('',item)):
						streetNumber = item
					# Otherwise if it is just a number, must be a street number
					elif item.isdigit():
						streetNumber = item

					# Remove all directional identifiers (since aren't consistently specified)
					elif item not in directions:
						# Concatenate to previously stored "streetName" variable
						if streetName:
							streetName = streetName + ' ' + item
						else:
							streetName = item

				# String contains both street and unit address
				elif hasStreet:

					# If the first item is or has a number, probably a street number
					if IDX == 0 and len(patternAlpha.sub('',item)):
						streetNumber = item
					# Otherwise if it is just a number, must be a street number
					elif item.isdigit() and IDX < unitIDX:
						streetNumber = item

					# If it is prior to unitIDX must be part of street name
					# Also, again, remove all directions, since not consistently specified
					elif IDX < unitIDX and item not in directions:
						# Concatenate to previously stored "streetName" variable
						if streetName:
							streetName = streetName + ' ' + item
						# Otherwise initialize!
						elif item:
							streetName = item

					else:
						unitNumber = item

				# String contains only a unit address
				else:
					unitNumber = item

		parsedAddress = {}
		if hasStreet:
			parsedAddress['streetNumber'] = streetNumber
			parsedAddress['streetName'] = streetName
			parsedAddress['streetType'] = streetType
		if hasUnit:
			parsedAddress['unitType'] = unitType
			parsedAddress['unitNumber'] = unitNumber

		return parsedAddress

	def combineParsedAddresses(self, parsedAddress1, parsedAddress2):

		parsedAddress = {'streetNumber': '', 'streetName': '', 'streetType': '', 'unitType': '', 'unitNumber': ''}
		# Usual case, address1 is street number + street name; address2 is unit and unit number
		if len(parsedAddress1) == 3 and len(parsedAddress2) == 2:
			parsedAddress = parsedAddress1
			parsedAddress['unitType'] = parsedAddress2['unitType']
			parsedAddress['unitNumber'] = parsedAddress2['unitNumber']
		# Order has been switched
		elif len(parsedAddress2) == 3 and len(parsedAddress1) == 2:
			parsedAddress = parsedAddress1
			parsedAddress['unitType'] = parsedAddress1['unitType']
			parsedAddress['unitNumber'] = parsedAddress1['unitNumber']	
		# Entire address is in address1 variable	
		elif len(parsedAddress1) == 5 and not len(parsedAddress2):
			parsedAddress = parsedAddress1
		# Entire address is in address2 variable
		elif len(parsedAddress2) == 5 and not len(parsedAddress1):
			parsedAddress = parsedAddress2
		# Otherwise skip this record...
		return parsedAddress


	def cleanAddresses(
		self,
		inDir, inDSN, 
		keepVars,
		addressVarsList,
		addressVarsTypeList,
		output_csv = False,
		outDir = None,
		outDSN = None
	):

		# Read in data
		os.chdir(inDir)
		# Make sure everything is read as STRING (especially important for zip codes...)
		df = pd.read_csv(inDSN, dtype = str)

		# Join all address variables and get a unique-by-address dataset
		df = df.loc[:,addressVarsList + keepVars]

		df['address'] = df.apply(lambda x: '`^'.join([str(x[var]) for var in addressVarsList + keepVars]), axis = 1)
		addresses = df['address'].unique()
		addressArray = pd.DataFrame(
			[address.split('`^')[:len(addressVarsList + keepVars)] for address in addresses], 
			columns = addressVarsTypeList + keepVars,
			dtype = str
		)

		if 'address1' in addressVarsTypeList:
			parsedAddresses1 = [self.parseStreetAddress(string,'street') for string in addressArray['address1']]
		if 'address2' in addressVarsList:
			parsedAddresses2 = [self.parseStreetAddress(string,'unit') for string in addressArray['address2']]
		# Address is provided in single variable
		if 'address' in addressVarsTypeList:
			parsedAddresses = [self.parseStreetAddress(string,'both') for string in addressArray['address']]
		# Address is provided in two different variables, need to combine
		else:
			parsedAddresses = [self.combineParsedAddresses(parsedAddresses1[IDX], parsedAddresses2[IDX]) for IDX in range(len(addressArray))]

		cleanAddresses = pd.DataFrame(parsedAddresses)

		# For variables that are included separately (i.e. not a combined 'address1','address2', or 'address' type variable)
		# Just run the basic cleaning procedure (remove special characters, abbreviate, uppercase, etc)
		for varType in self.varTypes:
			if varType in addressVarsTypeList and varType != 'zip':
				cleanAddresses[varType] = list(map(self.cleanAddressString, addressArray[varType]))
			# Exception is zip code, just want to take first 5 digits since the remaining 5 aren't always included
			elif varType in addressVarsTypeList:
				cleanAddresses['zip'] = [zip[0:5] for zip in addressArray['zip']]

		# Add the (id or other) variables we want to keep
		cleanAddresses[keepVars] = addressArray.loc[:,keepVars]

		if output_csv:
			if not outDir:
				outDir = askdirectory()
			if not outDSN:
				outDSN = inDSN + 'cleanAddresses.csv'
			cleanAddresses.to_csv(os.path.join(outDir,outDSN), index = False, encoding = 'utf-8')

		return cleanAddresses


	def checkJaro(self,string1,string2):
		match = 0
		if not pd.isnull(string1) and not pd.isnull(string2):
			words1, words2 = string1.split(), string2.split()
			for word1 in words1:
				for word2 in words2:
					if jellyfish.jaro_distance(word1,word2) > self.jaro_th:
						match = 1
		return match


	def checkMerge(self,row):
		match = 0
		check = 0
		if row['_merge'] == 'both':
			if tuple(row[self.hardByVars].values) in self.one2many:
				# Match by one of soft variables
				for softByVar in self.softByVars:
					# Unit or street number
					if softByVar != 'name':
						if row[softByVar + '_x'] == row[softByVar + '_y']:
							match = 1
						elif not pd.isnull(row[softByVar + '_x']) and not pd.isnull(row[softByVar + '_y']):
							check  = 1
					# Name
					else:
						match = self.checkJaro(row['name_x'], row['name_y'])

			else:
				match = 1
				for softByVar in self.softByVars:
					# Unit or street number
					if softByVar != 'name':
						if row[softByVar + '_x'] != row[softByVar + '_y']:
							if not pd.isnull(row[softByVar + '_x']) and not pd.isnull(row[softByVar + '_y']):
								check = 1
					# Name
					else:
						check = 1 - self.checkJaro(row['name_x'], row['name_y'])

		elif self.checkName:
			match = self.checkJaro(row['name_x'], row['name_y'])
		
		return [match, check]


	def matchAddresses(self, keep, hardByVars, softByVars = None, checkName = False, jaro_th = 1, output_csv = True, outDir = None, outDSN = None):

		self.hardByVars = hardByVars
		self.softByVars = softByVars
		self.checkName = checkName
		self.jaro_th = jaro_th

		cleanAddresses1 = self.cleanAddresses(
			self.inDir1, self.inDSN1, 
			self.keepVars1, 
			self.addressVarsList1, self.addressVarsTypeList1
		)
		cleanAddresses2 = self.cleanAddresses(
			self.inDir2, self.inDSN2, 
			self.keepVars2, 
			self.addressVarsList2, self.addressVarsTypeList2
		)

		# Determine what kind of merge is being performed based on user input
		if keep == '1':
			mergeType = 'left'
		elif keep == '2':
			mergeType = 'right'
		else:
			mergeType = 'outer'

		# Perform merge
		mergedAddresses = cleanAddresses1.merge(
			cleanAddresses2, 
			on = hardByVars, 
			how = mergeType,
			indicator = True
		)

		# Get one-to-one, one-to-many and many-to-many ID combinations
		keepVarsSizes = mergedAddresses.groupby(hardByVars).size()
		self.one2many = keepVarsSizes.loc[:,keepVarsSizes > 1]
		
		mergedAddresses[['match','check']]= mergedAddresses.apply(lambda row: pd.Series(self.checkMerge(row)), axis = 1)

		mergedOutput = mergedAddresses.loc[mergedAddresses['match'] == 1]

		if output_csv:
			if not outDir:
				outDir = inDir
			if not outDSN:
				outDSN = 'matchedAddresses.csv'
			mergedOutput.to_csv(os.path.join(outDir,outDSN), index = False, encoding = 'utf-8')

		return mergedOutput

# Create matchAddresses class
clnAdd = matchAddresses(
	# Directory of first dataset
	inDir1 = '/Users/josebolorinos/Google Drive (jbolorin@stanford.edu)/EVP Private/Data/Yelp Data', 
	# File name of first dataset
	inDSN1 = 'IrvineRanch_allYelpData.csv', 
	# Extra variables to keep from first dataset
	keepVars1 = ['categories','is_closed','price','rating','review_count'],
	# Address variable names in first dataset (as they are)
	addressVarsList1 = ['address1','address2','city','zip_code','name'], 
	# Types of address variables in the first dataset 
	# (can be 'address1','address2','address','streetNumber','streetName','streetType','unitName','unitType','city','zip','name')
	addressVarsTypeList1 = ['address1','address2','city','zip','name'],
	# Directory of second dataset
	inDir2 = '/Users/josebolorinos/Google Drive (jbolorin@stanford.edu)/EVP Private/Data/Yelp Data', 
	# File name of second dataset
	inDSN2 = 'IRWD Master (0-6).csv', 
	# Extra variables to keep from second dataset
	keepVars2 = ['ACCT_ID'],
	# Address variable names in second dataset (as they are)
	addressVarsList2 = ['CITY','ADDRESS','POSTAL','CUST_NAME'], 
	# Types of address variables in the second dataset 
	# (can be 'address1','address2','address','streetNumber','streetName','streetType','unitName','unitType','city','zip','name')
	addressVarsTypeList2 = ['city','address','zip','name']	
)

# Execute the matchAddresses method on the matchAddresses class (only outputs observations where "match" = 1)
# NOTE: this does NOT guarantee a unique match, it is possible for multiple pairs to match each other
clnAdd.matchAddresses(
	# Which dataset is being "kept" can be either '1','2', or 'both', this will determine how matches are searched for
	keep = '2',
	# Variables that MUST be equal to consider the pair a match (from addressVarsTypeLists defined above)
	hardByVars = ['zip','streetName','streetNumber'],
	# Variables that will also be checked for a match 
	# (if they aren't equal, then they will be output, but a "check" variable will be set to 1 to flag them)
	softByVars = ['unitNumber','name'],
	# Relevant to businesses, if the hardByVars don't match, should the business name be used to check a match?
	# NOTE: will perform jaro similarity between two strings on EACH word in the business name and set match = 1 if any of the words
	# are above the threshold
	checkName = True,
	# Minimum word on word Jaro similarity to be considered a match (default is 1)
	jaro_th = 0.9,
	# Should a csv be output? Default True
	output_csv = True, 
	# If outputing a csv, output directory, default is input directory
	outDir = '/Users/josebolorinos/Google Drive (jbolorin@stanford.edu)/EVP Private/Data/Yelp Data',
	# If outputing a csv, output filename, default is "matchedAddresses"
	outDSN = 'IrvineRanchYelp_0-6.csv'
)



