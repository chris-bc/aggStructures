import csv
import sys

# Prepare primary output file
outFileName = 'output.csv'
rFileName = 'relationships.csv'
if (len(sys.argv) > 1):
	outFileName = sys.argv[1]
	if (len(sys.argv) > 2):
		rFileName = sys.argv[2]
outFile = open(outFileName, "wb")
outWriter = csv.writer(outFile)

print "Writing MBLT load file to " + outFileName
print "Writing MBLT relationships file to " + rFileName
print "Processing levels..."

# Determine levels
classns = ["Employment Class","Business Foreign Ownership","ANZSIC"]
level1 = ["All Businesses"]
levels = [level1]
level2 = []
for classn in classns:
	level2.append(classn)
levels.append(level2)
# level 3 - e by b, e by a, b by a
level3 = []
for x in range(2):
	for y in range(2-x):
		level3.append(classns[x]+" by "+classns[y+1+x])
levels.append(level3)
level4 = []
# simple level 4
level4.append(classns[0]+" by "+classns[1]+" by "+classns[2])
levels.append(level4)

# Write MBLT Level header
outWriter.writerow(['HEADER:3.2.1:HierarchyLevel:7','Class:','Id:','attr:Name','attr:Description','attr:AltId.AlternateID.id','attr:AppliesTo.ClassReference.id','attr:IsMemberOf.GroupingMembership.id','attr:PrincipalPath','relType:HasValuesFrom','relId:HasValuesFrom','relType:IsCopyOf','relId:IsCopyOf','relType:IspartofList','relId:IspartofList','relType:MayBeDefinedBy','relId:MayBeDefinedBy'])

# Assign level IDs, principal paths (first path in a level) and parents
levelCount = 1
levelId = 1
nextParentId = 1
lastParentId = 1
principal = ""
parentType = ""
parentId = ""
for level in levels:
	itemInLevel = 1
	for item in level:
		if (itemInLevel == 1):
			principal = "TRUE"
			nextParentId = levelId
		else:
			principal = "FALSE"
		if (levelCount > 1):
			parentType = "HierarchyLevel"
			parentId = "L-"+str(lastParentId)

		outWriter.writerow([None,'HierarchyLevel','L-'+str(levelId),item,item,None,None,None,principal,None,None,None,None,parentType,parentId,None,None])
		levelId = levelId + 1
		itemInLevel = itemInLevel + 1
	levelCount = levelCount + 1
	lastParentId = nextParentId
outWriter.writerow([])

print "Parsing CodeLists..."

# Read in CodeLists
anzsic = []
with open("codeitems-anzsic.csv") as csvfile:
	reader = csv.reader(csvfile)
	newRow = []
	for row in reader:
		# Fix issues caused by commas in the description
		newRow.append(row[0])
		newRow.append(row[1])
		for i in range(len(row)-3):
			newRow[1] = newRow[1] + "," + row[i+2]
		newRow.append(row[len(row)-1])
		anzsic.append(newRow)

forOwn = []
with open("codeitems-business-foreign-ownership.csv") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		forOwn.append(row)

empClass = []
with open("codeitems-employment-class.csv") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		empClass.append(row)

print "Creating aggItems..."

# Create AggItems and assign codeitem IDs
eTotalCodeId = 0
fTotalCodeId = 0
codeId=1
aggItems = []
aiId = 1
ai = {
	"id":aiId,
	"name":"All businesses",
	"level":1,
	"rule":"1=1"
}
aggItems.append(ai)
aiId = aiId + 1

print "empClass"

eAggItems = []
for eItem in empClass:
	ai = {
		"id":aiId,
		"name":eItem[1].strip(),
		"level":2,
		"rule":"empClassRV = '"+eItem[2].strip() + "'",
		"parents":[1],
		"codes":[codeId],
		"codeUrn":(eItem[0].strip())
	}
	eAggItems.append(ai)
	aiId = aiId + 1
	if (eItem[2].strip() == "A0"):
		eTotalCodeId = codeId
	codeId = codeId + 1

print "forOwn"

fAggItems = []
for fItem in forOwn:
	ai = {
		"id":aiId,
		"name":fItem[1].strip(),
		"level":3,
		"rule":"forOwnRV = '"+fItem[2].strip() + "'",
		"parents":[1],
		"codes":[codeId],
		"codeUrn":(fItem[0].strip())
	}
	fAggItems.append(ai)
	aiId = aiId + 1
	if (fItem[2].strip() == "A0"):
		fTotalCodeId = codeId
	codeId = codeId + 1

print "ANZSIC"

aAggItems = []
for aItem in anzsic:
	ai = {
		"id":aiId,
		"name":aItem[1].strip(),
		"level":4,
		"rule":"anzsicRV = '"+aItem[2].strip() + "'",
		"parents":[1],
		"codes":[codeId],
		"codeUrn":(aItem[0].strip())
	}
	aAggItems.append(ai)
	aiId = aiId + 1
	codeId = codeId + 1

print "empClass-forOwn and empClass-ANZSIC"

efAggItems = []
eaAggItems = []
for eAggItem in eAggItems:
	for fAggItem in fAggItems:
		ai = {
			"id":aiId,
			"eid":eAggItem["id"],
			"fid":fAggItem["id"],
			"name":eAggItem["name"] + " by " + fAggItem["name"],
			"level":5,
			"rule":eAggItem["rule"] + " and " + fAggItem["rule"],
			"parents":[eAggItem["id"], fAggItem["id"]],
			"codes":eAggItem["codes"] + fAggItem["codes"]
		}
		efAggItems.append(ai)
		aiId = aiId + 1
	
	for aAggItem in aAggItems:
		ai = {
			"id":aiId,
			"eid":eAggItem["id"],
			"aid":aAggItem["id"],
			"name":eAggItem["name"] + " by " + aAggItem["name"],
			"level":6,
			"rule":eAggItem["rule"] + " and " + aAggItem["rule"],
			"parents":[eAggItem["id"], aAggItem["id"]],
			"codes":eAggItem["codes"] + aAggItem["codes"] + [fTotalCodeId]
		}
		eaAggItems.append(ai)
		aiId = aiId + 1

print "forOwn-ANZSIC"

faAggItems = []
for fAggItem in fAggItems:
	for aAggItem in aAggItems:
		ai = {
			"id":aiId,
			"fid":fAggItem["id"],
			"aid":aAggItem["id"],
			"name":fAggItem["name"] + " by " + aAggItem["name"],
			"level":7,
			"rule":fAggItem["rule"] + " and " + aAggItem["rule"],
			"parents":[fAggItem["id"], aAggItem["id"]],
			"codes":fAggItem["codes"] + aAggItem["codes"] + [eTotalCodeId]
		}
		faAggItems.append(ai)
		aiId = aiId + 1

print "Lowest level of aggregation"

# Create e-f-a aggItems without parents initially - Assign them later
efaAggItems = []
for e in eAggItems:
	for f in fAggItems:
		for a in aAggItems:
			ai = {
				"id":aiId,
				"eid":e["id"],
				"fid":f["id"],
				"aid":a["id"],
				"name":e["name"] + " by " + f["name"] + " by " + a["name"],
				"level":8,
				"rule":e["rule"] + " and " + f["rule"] + " and " + a["rule"],
				"parents":[],
				"codes":e["codes"] + f["codes"] + a["codes"]
			}
			efaAggItems.append(ai)
			aiId = aiId + 1

print "Processing parents"

# Assign parents to e-f-a aggItems
for efa in efaAggItems:
	for ef in efAggItems:
		if (efa["eid"] == ef["eid"] and efa["fid"] == ef["fid"]):
			efa["parents"].append(ef["id"])
	for ea in eaAggItems:
		if (efa["eid"] == ea["eid"] and efa["aid"] == ea["aid"]):
			efa["parents"].append(ea["id"])
	for fa in faAggItems:
		if (efa["fid"] == fa["fid"] and efa["aid"] == fa["aid"]):
			efa["parents"].append(fa["id"])

# TODO Now loop back through a,f&eAggItems and assign e/fTotalCodeId
for e in eAggItems:
	e["codes"].append(fTotalCodeId)
for f in fAggItems:
	f["codes"].append(eTotalCodeId)
for a in aAggItems:
	a["codes"].append(fTotalCodeId)
	a["codes"].append(eTotalCodeId)
aggItems[0]["codes"] = [fTotalCodeId, eTotalCodeId]

print "Writing aggregation items"

# Finally combine all aggItem decompositions together
aggItems = aggItems + eAggItems + fAggItems + aAggItems + efAggItems + eaAggItems + faAggItems + efaAggItems

# Write MBLT header for AggItems
outWriter.writerow(['HEADER:3.2.1:AggregationItem:3','Class:','Id:','attr:Name','attr:Description','attr:Altid.AlternateID.id','attr:Code','attr:IsMemberOf.GroupingMembership.id','attr:ProcessLogic','relType:HasFilter','relId:HasFilter','relType:HasLevel','relId:HasLevel','relType:IsCopyOf','relId:IsCopyOf','relType:IschildOf','relId:IschildOf','relType:MayReference','relId:MayReference','relType:TakesMeaningFrom','relId:TakesMeaningFrom'])

# Write MBLT records for aggItems
for aggItem in aggItems:
	thisRow = [None,'AggregationItem','AI-'+str(aggItem["id"]),aggItem["name"]]
	thisRow = thisRow + [aggItem["name"],None,str(aggItem["id"]),None,None,'Rule','R-'+str(aggItem["id"])]
	thisRow = thisRow + ['HierarchyLevel','L-'+str(aggItem["level"]),None,None]
	extraRows = 0
	if ("parents" in aggItem):
		extraRows = len(aggItem["parents"])
	if ("codes" in aggItem and len(aggItem["codes"]) > extraRows):
		extraRows = len(aggItem["codes"])
	
	if (extraRows == 0):
		thisRow = thisRow + [None,None,None,None,None]
		outWriter.writerow(thisRow)
	else:
		firstExtra = 1
		for i in range(extraRows):
			thisParent = ""
			thisCode = ""
			if ("codes" in aggItem and i< len(aggItem["codes"])):
				thisCode = format(aggItem["codes"][i], '05')
			if ("parents" in aggItem and i< len(aggItem["parents"])):
				thisParent = str(aggItem["parents"][i])
			if (firstExtra == 0):
				thisRow = [None,None,None,None,None,None,None,None,None,None,None,None,None,None,None]
			firstExtra = 0
			if (len(thisParent)>0):
				thisRow = thisRow + ['AggregationItem','AI-'+thisParent]
			else:
				thisRow = thisRow + [None,None]
			if (len(thisCode) > 0):
				thisRow = thisRow + ['CodeItem','CD-'+thisCode]
			else:
				thisRow = thisRow + [None,None]
			thisRow = thisRow + [None,None]
			outWriter.writerow(thisRow)

print "Processing rules..."

# Write MBLT header for rules
outWriter.writerow(['HEADER:3.2.1:Rule:24','Class:','Id:','attr:Name','attr:Description','attr:Algorithm','attr:AltId.AlternateID.id','attr:IsMemberOf.GroupingMembership.id','attr:RuleType','attr:SystemExecutableIndicator','relType:Has','relId:Has','relType:HasInputs','relId:HasInputs','relType:HasOutputs','relId:HasOutputs','relType:IsAuthoredBy','relId:IsAuthoredBy','relType:IsCopyOf','relId:IsCopyOf','relType:IsDefinedBy','relId:IsDefinedBy'])

# Write MBLT records for rules
for aggItem in aggItems:
	outWriter.writerow([None,'Rule','R-'+str(aggItem["id"]),'Filter '+aggItem["name"],'Filter '+aggItem["name"],aggItem["rule"],None,None,'Filter',None,'SystemLanguage','R',None,None,None,None,'StatisticalProgram','SP-001',None,None,None,None])

print "Processing hierarchy specification..."

# Write MBLT Header for Hierarchy spec
outWriter.writerow(['HEADER:3.2.1:HierarchySpecification:6','Class:','Id:','attr:Name','attr:Description','attr:Altid.AlternateID.id','attr:IsMemberOf.GroupingMembership.id','relType:Has','relId:Has','relType:IsBasedOn','relId:IsBasedOn','relType:IsCopyOf','relId:IsCopyOf','relType:IsImplementedAs','relId:IsImplementedAs','relType:IsIndexedAs','relId:IsIndexedAs','relType:RelatesTo','relId:RelatesTo','relType:Root','relId:Root'])

# Write MBLT Hierarchy Spec records
outWriter.writerow([None,'HierarchySpecification','HS-1','Businesses by employment class by foreign ownership by industry','Businesses by employment class by foreign ownership by industry',None,None,'HierarchyLevel','L-1',None,None,None,None,None,None,None,None,None,None,'HierarchyLevel','L-1'])
outWriter.writerow([None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,'AggregationItem','AI-1'])
for l in range(7):
	outWriter.writerow([None,None,None,None,None,None,None,'HierarchyLevel','L-'+str(l+1),None,None,None,None,None,None,None,None,None,None,None,None])
for a in aggItems:
	outWriter.writerow([None,None,None,None,None,None,None,'AggregationItem','AI-'+str(a["id"]),None,None,None,None,None,None,None,None,None,None,None,None])
outFile.close()

print "Creating relationships file " + rFileName + "..."

# Output Relationships
ofile = open(rFileName, "wb")
writer = csv.writer(ofile)
writer.writerow(['Class','ID','URN'])
for e in eAggItems:
	writer.writerow(['CodeItem', 'CD-'+format(e["codes"][0], '05'), e["codeUrn"]])
for f in fAggItems:
	writer.writerow(['CodeItem', 'CD-'+format(f["codes"][0], '05'), f["codeUrn"]])
for a in aAggItems:
	writer.writerow(['CodeItem', 'CD-'+format(a["codes"][0], '05'), a["codeUrn"]])
ofile.close()
