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

# Determine levels
classns = ["Employment Class","Business Foreign Ownership","ANZSIC Division"]
classnShortName = ["empClass","forOwn","A06 Div","A06 SubDiv","A06 Group","A06 Class"]
level1 = ["All Businesses"]
levels = [level1]
level2 = []
for classn in classns:
	level2.append(classn)
levels.append(level2)
# level 3 - e by b, e by a, b by a, a-subdiv
level3 = []
for x in range(2):
	for y in range(2-x):
		level3.append(classns[x]+" by "+classns[y+1+x])
level3.append("ANZSIC Subdivision")
levels.append(level3)
# level 4 - e-b-a-div, e-a-a-subdiv, b-a-a-subdiv
level4 = []
level4.append(classns[0] + " by " + classns[1] + " by " + classns[2])
level4.append(classns[0] + " by ANZSIC Subdivision")
level4.append(classns[1] + " by ANZSIC Subdivision")
levels.append(level4)
# simple level 5
level5 = []
level5.append(classns[0]+" by "+classns[1]+" by ANZSIC Subdivision")
levels.append(level5)

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

# Read in CodeLists
anzsic = []
with open("codeitems-anzsic.csv") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		newRow = []
		# Fix issues caused by commas in the description
		newRow.append(row[0])
		newRow.append(row[1])
		newRow.append(row[2].strip())
		i = 3
		while len(row[i].strip()) > 1 and not row[i].strip().isdigit():
			# It must be a spurious comma
			newRow[len(newRow)-1] = newRow[len(newRow)-1] + ", " + row[i].strip()
			i = i + 1
		# Finally we've come to the parent code value
		for n in range(3):
			newRow.append(row[i].strip())
			i = i + 1
		while (not row[i].strip().isdigit()):
			newRow[len(newRow)-1] = newRow[len(newRow)-1] + ", " + row[i].strip()
			i = i + 1
		newRow.append(row[i].strip())
		anzsic.append(newRow)
print "Read in " + str(len(anzsic)) + " ANZSIC CodeItems"

forOwn = []
with open("codeitems-business-foreign-ownership.csv") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		forOwn.append(row)
print "Read in " + str(len(forOwn)) + " " + classns[1] + " CodeItems"

empClass = []
with open("codeitems-employment-class.csv") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		empClass.append(row)
print "Read in " + str(len(empClass)) + " " + classns[0] + " CodeItems"

# Create AggItems and assign codeitem IDs
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

codeLists = [empClass, forOwn, anzsic]
aggLevels = []
for cl in range(len(codeLists)):
	cLevels = [[]]
	cLevel = 0
	lastRootValue = ""
	tempRV = ""
	if cl == 0:
		tempRV = "empClassRV"
	elif cl == 1:
		tempRV = "forOwnRV"
	elif cl == 2:
		tempRV = "anzsicRV"
	for ci in codeLists[cl]:
		if int(ci[0]) == 2 and ci[3].strip() != lastRootValue:
			# We've found a new root node
			cLevels[0].append({
				"id":aiId,
				"name":classnShortName[cl] + ": " + ci[2].strip(),
				"level":2+cl,
				"parents":[1],
				"codes":[codeId],
				"codeUrn":ci[1].strip(),
				"value":ci[3].strip(),
				"rvUrn":tempRV
			})
			aiId = aiId + 1
			codeId = codeId + 1
			lastRootValue = ci[3].strip()
		if int(ci[0]) > cLevel:
			# Create a new level in cLevels for the current level of the CodeList
			cLevel = int(ci[0])
			cLevels.append([])
		cLevels[cLevel-1].append({
			"id":aiId,
			"name":classnShortName[cl-2+cLevel] + ": " + ci[5].strip(),
			"level":2+cl,
			"parents":[],
			"codes":[codeId],
			"codeUrn":ci[4].strip(),
			"value":ci[6].strip(),
			"parentValue":ci[3].strip(),
			"rvUrn":tempRV
		})
		aiId = aiId + 1
		codeId = codeId + 1
	aggLevels.append(cLevels)
	
	for i in range(len(cLevels)-1,-1,-1):
		for j in range(len(cLevels[i])):
			if i == len(cLevels)-1:
				# Dealing with the lowest level - use the value provided
				cLevels[i][j]["selector"] = cLevels[i][j]["value"]
			else:
				# Find values of children with me as their parent
				childValues = []
				for k in range(len(cLevels[i+1])):
					if cLevels[i+1][k]["parentValue"] == cLevels[i][j]["value"]:
						childValues.append(cLevels[i+1][k]["selector"])
						cLevels[i+1][k]["parents"].append(cLevels[i][j]["id"])
				cLevels[i][j]["selector"] = ','.join(childValues)
	
	# Produce some metrics
	print "Processed aggregation items for " + classns[cl]
	print "Number of levels: " + str(len(aggLevels[cl]))
	for i in range(len(aggLevels[cl])):
		print "Number of items in level " + str(i) + ": " + str(len(aggLevels[cl][i]))

efAggItems = []
eaAggItems = []
# Use level 2 of empClass and forOwn
for eAggItem in aggLevels[0][1]:
	for fAggItem in aggLevels[1][1]:
		ai = {
			"id":aiId,
			"eid":eAggItem["id"],
			"fid":fAggItem["id"],
			"name":eAggItem["name"] + " by " + fAggItem["name"],
			"level":5,
			"rule":eAggItem["rvUrn"] + " in (" + eAggItem["selector"] + ") and " + fAggItem["rvUrn"] + " in (" + fAggItem["selector"] + ")",
			"parents":[eAggItem["id"], fAggItem["id"]],
			"codes":eAggItem["codes"] + fAggItem["codes"]
		}
		efAggItems.append(ai)
		aiId = aiId + 1
	
	# ANZSIC Division is level 1
	for aAggItem in aggLevels[2][0]:
		# Rule and related codes need to include forOwn root selector and codeId
		ai = {
			"id":aiId,
			"eid":eAggItem["id"],
			"aid":aAggItem["id"],
			"name":eAggItem["name"] + " by " + aAggItem["name"],
			"level":6,
			"rule":eAggItem["rvUrn"] + " in (" + eAggItem["selector"] + ") and " + aAggItem["rvUrn"] + " in (" + aAggItem["selector"] + ")  and " + aggLevels[1][0][0]["rvUrn"] + " in (" + aggLevels[1][0][0]["selector"] + ")",
			"parents":[eAggItem["id"], aAggItem["id"]],
			"codes":eAggItem["codes"] + aAggItem["codes"] + aggLevels[1][0][0]["codes"]
		}
		eaAggItems.append(ai)
		aiId = aiId + 1

print "Produced " + str(len(efAggItems)) + " e-f aggItems and " + str(len(eaAggItems)) + " e-a aggItems"

faAggItems = []
# Using level 2 of forOwn and level 1 of ANZSIC
# Using level 1 of empClass for total in rule and codeItems
for fAggItem in aggLevels[1][1]:
	for aAggItem in aggLevels[2][0]:
		ai = {
			"id":aiId,
			"fid":fAggItem["id"],
			"aid":aAggItem["id"],
			"name":fAggItem["name"] + " by " + aAggItem["name"],
			"level":7,
			"rule":fAggItem["rvUrn"] + " in (" + fAggItem["selector"] + ") and " + aAggItem["rvUrn"] + " in (" + aAggItem["selector"] + ") and " + aggLevels[0][0][0]["rvUrn"] + " in (" + aggLevels[0][0][0]["selector"] + ")",
			"parents":[fAggItem["id"], aAggItem["id"]],
			"codes":fAggItem["codes"] + aAggItem["codes"] + aggLevels[0][0][0]["codes"]
		}
		faAggItems.append(ai)
		aiId = aiId + 1

print "Produced " + str(len(faAggItems)) + " f-a aggItems"

# Use level 2 of ANZSIC and level 1 of the others
# Use IDs already assigned for ANSZIC SubDiv
aaAggItems = []
for aAggItem in aggLevels[2][1]:
	aaAggItems.append({
		"id":aAggItem["id"],
		"name":aAggItem["name"],
		"level":8,
		"rule":aAggItem["rvUrn"] + " in (" + aAggItem["selector"] + ") and " + aggLevels[0][0][0]["rvUrn"] + " in (" + aggLevels[0][0][0]["selector"] + ") and " + aggLevels[1][0][0]["rvUrn"] + " in (" + aggLevels[1][0][0]["selector"] + ")",
		"parents":aAggItem["parents"],
		"codes":aAggItem["codes"] + aggLevels[0][0][0]["codes"] + aggLevels[1][0][0]["codes"]
	})

print "Produced " + str(len(aaAggItems)) + " a-a aggItems"

aaeAggItems = []
aafAggItems = []
for aAggItem in aggLevels[2][1]:
	for eAggItem in aggLevels[0][1]:
		aaeAggItems.append({
			"id":aiId,
			"aid":aAggItem["parents"][0],
			"aaid":aAggItem["id"],
			"eid":eAggItem["id"],
			"eaid":"",
			"name":aAggItem["name"] + " by " + eAggItem["name"],
			"level":9,
			"rule":aAggItem["rvUrn"] + " in (" + aAggItem["selector"] + ") and " + eAggItem["rvUrn"] + " in (" + eAggItem["selector"] + " and " + aggLevels[1][0][0]["rvUrn"] + " in (" + aggLevels[1][0][0]["selector"] + ")",
			"parents":[aAggItem["id"]],
			"codes":aAggItem["codes"] + eAggItem["codes"] + aggLevels[1][0][0]["codes"]
		})
		aiId = aiId + 1
	
	for fAggItem in aggLevels[1][1]:
		aafAggItems.append({
			"id":aiId,
			"aid":aAggItem["parents"][0],
			"aaid":aAggItem["id"],
			"faid":"",
			"fid":fAggItem["id"],
			"name":aAggItem["name"] + " by " + fAggItem["name"],
			"level":10,
			"rule":aAggItem["rvUrn"] + " in (" + aAggItem["selector"] + ") and " + fAggItem["rvUrn"] + " in (" + fAggItem["selector"] + " and " + aggLevels[0][0][0]["rvUrn"] + " in (" + aggLevels[0][0][0]["selector"] + ")",
			"parents":[aAggItem["id"]],
			"codes":aAggItem["codes"] + fAggItem["codes"] + aggLevels[0][0][0]["codes"]
		})
		aiId = aiId + 1

print "Produced " + str(len(aaeAggItems)) + " a-a-e aggItems and " + str(len(aafAggItems)) + " a-a-f aggItems"

for x in aaeAggItems:
	for y in eaAggItems:
		if y["eid"] == x["eid"] and y["aid"] == x["aid"]:
			x["eaid"] = y["id"]
			x["parents"].append(y["id"])

for x in aafAggItems:
	for y in faAggItems:
		if y["fid"] == x["fid"] and y["aid"] == x["aid"]:
			x["faid"] = y["id"]
			x["parents"].append(y["id"])

# Create e-f-a aggItems without parents initially - Assign them later
efaAggItems = []
for e in aggLevels[0][1]:
	for f in aggLevels[1][1]:
		for a in aggLevels[2][0]:
			ai = {
				"id":aiId,
				"eid":e["id"],
				"fid":f["id"],
				"aid":a["id"],
				"name":e["name"] + " by " + f["name"] + " by " + a["name"],
				"level":11,
				"rule":e["rvUrn"] + " in (" + e["selector"] + ") and " + f["rvUrn"] + " in (" + f["selector"] + ") and " + a["rvUrn"] + " in (" + a["selector"] + ")",
				"parents":[],
				"codes":e["codes"] + f["codes"] + a["codes"]
			}
			efaAggItems.append(ai)
			aiId = aiId + 1

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

print "Produced " + str(len(efaAggItems)) + " e-f-a aggItems"

# Create e-f-a-subDiv aggItems without parents initially - Assign them later
efaaAggItems = []
for e in aggLevels[0][1]:
	for f in aggLevels[1][1]:
		for a in aggLevels[2][1]:
			ai = {
				"id":aiId,
				"eid":e["id"],
				"fid":f["id"],
				"aaid":a["id"],
				"aid":a["parents"][0],
				"name":e["name"] + " by " + f["name"] + " by " + a["name"],
				"level":12,
				"rule":e["rvUrn"] + " in (" + e["selector"] + ") and " + f["rvUrn"] + " in (" + f["selector"] + ") and " + a["rvUrn"] + " in (" + a["selector"] +")",
				"parents":[],
				"codes":e["codes"] + f["codes"] + a["codes"]
			}
			efaaAggItems.append(ai)
			aiId = aiId + 1

# Parents are efa, aae, aaf
for efaa in efaaAggItems:
	for efa in efaAggItems:
		if (efaa["eid"] == efa["eid"] and efaa["fid"] == efa["fid"] and efaa["aid"] == efa["aid"]):
			efaa["parents"].append(efa["id"])
	for aae in aaeAggItems:
		if (efaa["eid"] == aae["eid"] and efaa["aaid"] == aae["aaid"]):
			efaa["parents"].append(aae["id"])
	for aaf in aafAggItems:
		if (efaa["fid"] == aaf["fid"] and efaa["aaid"] == aaf["aaid"]):
			efaa["parents"].append(aaf["id"])

print "Produced " + str(len(efaaAggItems)) + " e-f-a-a aggItems"

# Now loop back through a,f&eAggItems and assign e/fTotalCodeId
for e in aggLevels[0][1]:
	e["codes"].append(aggLevels[1][0][0]["codes"][0])
	e["rule"] = e["rvUrn"] + " in (" + e["selector"] + ") and " + aggLevels[1][0][0]["rvUrn"] + " in (" + aggLevels[1][0][0]["selector"] + ")"
aggLevels[0][0][0]["codes"].append(aggLevels[1][0][0]["codes"][0])
aggLevels[0][0][0]["rule"] = aggLevels[1][0][0]["rvUrn"] + " in (" + aggLevels[1][0][0]["selector"] + ")"
for f in aggLevels[1][1]:
	f["codes"].append(aggLevels[0][0][0]["codes"][0])
	f["rule"] = f["rvUrn"] + " in (" + f["selector"] + ") and " + aggLevels[0][0][0]["rvUrn"] + " in (" + aggLevels[0][0][0]["selector"] + ")"
aggLevels[1][0][0]["codes"].append(aggLevels[0][0][0]["codes"][0])
aggLevels[1][0][0]["rule"] = aggLevels[0][0][0]["rvUrn"] + " in (" + aggLevels[0][0][0]["selector"] + ")"
for l in aggLevels[2]:
	for a in l:
		a["codes"].append(aggLevels[1][0][0]["codes"][0])
		a["codes"].append(aggLevels[0][0][0]["codes"][0])
		a["rule"] = a["rvUrn"] + " in (" + a["selector"] + ") and " + aggLevels[1][0][0]["rvUrn"] + " in (" + aggLevels[1][0][0]["selector"] + ") and " + aggLevels[0][0][0]["rvUrn"] + " in (" + aggLevels[0][0][0]["selector"] + ")"
aggItems[0]["codes"] = [aggLevels[1][0][0]["codes"][0], aggLevels[0][0][0]["codes"][0]]

for cl in aggLevels:
	for l in cl:
		aggItems = aggItems + l
aggItems = aggItems + efAggItems + eaAggItems + faAggItems + aaAggItems + aaeAggItems + aafAggItems + efaAggItems + efaaAggItems

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

# Write MBLT header for rules
outWriter.writerow([])
outWriter.writerow(['HEADER:3.2.1:Rule:24','Class:','Id:','attr:Name','attr:Description','attr:Algorithm','attr:AltId.AlternateID.id','attr:IsMemberOf.GroupingMembership.id','attr:RuleType','attr:SystemExecutableIndicator','relType:Has','relId:Has','relType:HasInputs','relId:HasInputs','relType:HasOutputs','relId:HasOutputs','relType:IsAuthoredBy','relId:IsAuthoredBy','relType:IsCopyOf','relId:IsCopyOf','relType:IsDefinedBy','relId:IsDefinedBy'])

# Write MBLT records for rules
for aggItem in aggItems:
	outWriter.writerow([None,'Rule','R-'+str(aggItem["id"]),'Filter '+aggItem["name"],'Filter '+aggItem["name"],aggItem["rule"],None,None,'Filter',None,'SystemLanguage','R',None,None,None,None,'StatisticalProgram','SP-001',None,None,None,None])

# Write MBLT Header for Hierarchy spec
outWriter.writerow([])
outWriter.writerow(['HEADER:3.2.1:HierarchySpecification:6','Class:','Id:','attr:Name','attr:Description','attr:Altid.AlternateID.id','attr:IsMemberOf.GroupingMembership.id','relType:Has','relId:Has','relType:IsBasedOn','relId:IsBasedOn','relType:IsCopyOf','relId:IsCopyOf','relType:IsImplementedAs','relId:IsImplementedAs','relType:IsIndexedAs','relId:IsIndexedAs','relType:RelatesTo','relId:RelatesTo','relType:Root','relId:Root'])

# Write MBLT Hierarchy Spec records
outWriter.writerow([None,'HierarchySpecification','HS-1','Businesses by employment class by foreign ownership by industry','Businesses by employment class by foreign ownership by industry',None,None,'HierarchyLevel','L-1',None,None,None,None,None,None,None,None,None,None,'HierarchyLevel','L-1'])
outWriter.writerow([None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,'AggregationItem','AI-1'])
for l in range(7):
	outWriter.writerow([None,None,None,None,None,None,None,'HierarchyLevel','L-'+str(l+1),None,None,None,None,None,None,None,None,None,None,None,None])
for a in aggItems:
	outWriter.writerow([None,None,None,None,None,None,None,'AggregationItem','AI-'+str(a["id"]),None,None,None,None,None,None,None,None,None,None,None,None])
outFile.close()

# Output Relationships
ofile = open(rFileName, "wb")
writer = csv.writer(ofile)
writer.writerow(['Class','ID','URN'])
for cl in aggLevels:
	for l in cl:
		for i in l:
			writer.writerow(['CodeItem', 'CD-'+format(i["codes"][0], '05'), i["codeUrn"]])
ofile.close()
