import csv

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

# Print MBLT Level header
print "HEADER:3.2.1:HierarchyLevel:7,Class:,Id:,attr:Name,attr:Description,attr:AltId.AlternateID.id,attr:AppliesTo.ClassReference.id,attr:IsMemberOf.GroupingMembership.id,attr:PrincipalPath,relType:HasValuesFrom,relId:HasValuesFrom,relType:IsCopyOf,relId:IsCopyOf,relType:IspartofList,relId:IspartofList,relType:MayBeDefinedBy,relId:MayBeDefinedBy"

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

		print ",HierarchyLevel,L-"+str(levelId)+","+item+","+item+",,,,"+principal+",,,,,"+parentType+","+parentId+",,"
		levelId = levelId + 1
		itemInLevel = itemInLevel + 1
	levelCount = levelCount + 1
	lastParentId = nextParentId
print

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


# Finally combine all aggItem decompositions together
aggItems = aggItems + eAggItems + fAggItems + aAggItems + efAggItems + eaAggItems + faAggItems + efaAggItems

# Print MBLT header for AggItems
print "HEADER:3.2.1:AggregationItem:3,Class:,Id:,attr:Name,attr:Description,attr:Altid.AlternateID.id,attr:Code,attr:IsMemberOf.GroupingMembership.id,attr:ProcessLogic,relType:HasFilter,relId:HasFilter,relType:HasLevel,relId:HasLevel,relType:IsCopyOf,relId:IsCopyOf,relType:IschildOf,relId:IschildOf,relType:MayReference,relId:MayReference,relType:TakesMeaningFrom,relId:TakesMeaningFrom"

# Print MBLT records for aggItems
for aggItem in aggItems:
	print ",AggregationItem,AI-"+str(aggItem["id"])+",\""+aggItem["name"]+"\",\"",
	print aggItem["name"]+"\",,"+str(aggItem["id"])+",,,Rule,R-"+str(aggItem["id"]),
	print ",HierarchyLevel,L-"+str(aggItem["level"])+",,,",
	extraRows = 0
	if ("parents" in aggItem):
		extraRows = len(aggItem["parents"])
	if ("codes" in aggItem and len(aggItem["codes"]) > extraRows):
		extraRows = len(aggItem["codes"])
	
	if (extraRows == 0):
		print ",,,,,"
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
				print ",,,,,,,,,,,,,,,",
			firstExtra = 0
			if (len(thisParent)>0):
				print "AggregationItem,AI-"+thisParent+",",
			else:
				print ",,",
			if (len(thisCode) > 0):
				print "CodeItem,CD-"+thisCode,
			else:
				print ",",
			print ",,"

# Print MBLT header for rules
print "HEADER:3.2.1:Rule:24,Class:,Id:,attr:Name,attr:Description,attr:Algorithm,attr:AltId.AlternateID.id,attr:IsMemberOf.GroupingMembership.id,attr:RuleType,attr:SystemExecutableIndicator,relType:Has,relId:Has,relType:HasInputs,relId:HasInputs,relType:HasOutputs,relId:HasOutputs,relType:IsAuthoredBy,relId:IsAuthoredBy,relType:IsCopyOf,relId:IsCopyOf,relType:IsDefinedBy,relId:IsDefinedBy"

# Print MBLT records for rules
for aggItem in aggItems:
	print ",Rule,R-"+str(aggItem["id"])+",\"Filter "+aggItem["name"]+"\",\"Filter "+aggItem["name"]+"\","+aggItem["rule"]+",,,Filter,,SystemLanguage,R,,,,,StatisticalProgram,SP-001,,,,"

# Print MBLT Header for Hierarchy spec
print "HEADER:3.2.1:HierarchySpecification:6,Class:,Id:,attr:Name,attr:Description,attr:Altid.AlternateID.id,attr:IsMemberOf.GroupingMembership.id,relType:Has,relId:Has,relType:IsBasedOn,relId:IsBasedOn,relType:IsCopyOf,relId:IsCopyOf,relType:IsImplementedAs,relId:IsImplementedAs,relType:IsIndexedAs,relId:IsIndexedAs,relType:RelatesTo,relId:RelatesTo,relType:Root,relId:Root"

# Print MBLT Hierarchy Spec records
print ",HierarchySpecification,HS-1,Businesses by employment class by foreign ownership by industry,Businesses by employment class by foreign ownership by industry,,,HierarchyLevel,L-1,,,,,,,,,,,HierarchyLevel,L-1"
print ",,,,,,,,,,,,,,,,,,,AggregationItem,AI-1"
for l in range(7):
	print ",,,,,,,HierarchyLevel,L-"+str(l+1)+",,,,,,,,,,,,"
for a in aggItems:
	print ",,,,,,,AggregationItem,AI-"+str(a["id"])+",,,,,,,,,,,,"

# Output Relationships
ofile = open('relationships.csv', "wb")
writer = csv.writer(ofile)
writer.writerow(['Class','ID','URN'])
for e in eAggItems:
	writer.writerow(['CodeItem', 'CD-'+format(e["codes"][0], '05'), e["codeUrn"]])
for f in fAggItems:
	writer.writerow(['CodeItem', 'CD-'+format(f["codes"][0], '05'), f["codeUrn"]])
for a in aAggItems:
	writer.writerow(['CodeItem', 'CD-'+format(a["codes"][0], '05'), a["codeUrn"]])
ofile.close()
