import matchAddresses as mAdd

# Create matchAddresses class
clnAdd = mAdd.matchAddresses(
	# Directory of first dataset
	inDir1 = '~/InputDirectory1', 
	# File name of first dataset
	inDSN1 = 'Dataset1.csv', 
	# Extra variables to keep from first dataset
	keepVars1 = ['categories','is_closed','price','rating','review_count'],
	# Address variable names in first dataset (as they are)
	addressVarsList1 = ['address1','address2','city','zip_code','name'], 
	# Types of address variables in the first dataset 
	# (can be 'address1','address2','address','streetNumber','streetName','streetType','unitName','unitType','city','zip','name')
	addressVarsTypeList1 = ['address1','address2','city','zip','name'],
	# Directory of second dataset
	inDir2 = '~/InputDirectory2', 
	# File name of second dataset
	inDSN2 = 'Dataset2.csv', 
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
	outDir = '~/OutputDirectory',
	# If outputing a csv, output filename, default is "matchedAddresses"
	outDSN = 'outputDataset.csv'
)
