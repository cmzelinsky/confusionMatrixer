# -*- coding: utf-8 -*-
## author : Courtney Zelinsky
## created : 5/13/14
##
## Call on cmd line with arg[1] = gs, arg[2] = engine output for comparison to create a Confusion Matrix
##
## Wishlist:
## "There were 2 minor warts I know of in the code.  
## 1)	It's insufficiently clear if columns are the gold or test set.
## 2)	There is no link from confusion matrix to details files."
##

import datetime, os, xml.dom.minidom
from xml.dom.minidom import parse
startTime = datetime.datetime.now()
path = "C:/Users/courtney.zelinsky/Desktop/"

##args = sys.argv
##gsPath = args[1]
##engineOutputPath = args[2]
##if not os.path.exists(gsPath) or if not os.path.exists(engineOutputPath):
##    raise Exception('Invalid path(s)')

def findPair(fname): 
    return fname[:-3] + 'out.xml'

## functions for splitting lists by the relevant splitter : http://stackoverflow.com/questions/4322705/split-a-list-into-nested-lists-on-a-value
##

def _itersplit(l, splitters):
    current = []
    for item in l:
        if item in splitters:
            yield current
            current = []
        else:
            current.append(item)
    yield current

def magicsplit(l, *splitters):
    return tuple([subl for subl in _itersplit(l, splitters) if subl])

##
## End of functions

##
## Begin processing...
##

## for doc in gsPath: 

parsedGSDoc = parse('C:/Users/courtney.zelinsky/Desktop/confMatrixTestTemplate.out-gs.xml')
parsedEngineDoc = parse('C:/Users/courtney.zelinsky/Desktop/confMatrixTestTemplate.out-engine.xml')               
                        
gsCodes = []
gsEntryNumsOnly = []
gsEntryNums = []
gsDic1 = {}
gsDic2 = {}
finalGSDic = {}
gsParent = []

##    
## Establishing the gold standard data structures
##

##  assmpt for now -- will throw a test in later: the gold standard set is perfect & 1:1 ###
    
gsCodeNodes = parsedGSDoc.getElementsByTagName('mm:code') #code node
for node in gsCodeNodes:
    gsCodes.append(node.getAttribute('code'))
    ### codes just looks like a list of all the codes in order of mim appearance ###

gsParent = parsedGSDoc.getElementsByTagName('mm:binding') #code's sister 'mm:binding' node
for item in gsParent:
    for child in item.getElementsByTagName('mm:narrativeBinding'):
        gsEntryNumsOnly.append(child.getAttribute('ref'))
        gsEntryNums.append(child.getAttribute('ref'))
    gsEntryNums.append('\n')
del gsEntryNums[-1]
### all the tokenization ref nums associated with the codes ###

gsEntryNumsGrouped = magicsplit(gsEntryNums, '\n')
gsEntryNumsGroupedTuple = tuple(tuple(x) for x in gsEntryNumsGrouped)
    ### which looks like ((u'entry_102'), (u'entry_7', u'entry_8', u'entry_9'), (u'entry_35', u'entry_36') ...) ###
    ### Helpful because you can see the scoping of a certain mim ... len(gsEntryNumsGroupedTuple[1]) -> 3 (tokens long) ###

goldWorkingData = zip(gsEntryNumsGroupedTuple, gsCodes)
gsWorkingData = tuple(goldWorkingData)
    ### which looks like ((('entry_102'), 'LAST_NAME'), (('entry_7', 'entry_8', 'entry_9'), 'AGE') ...) ###


for entry in gsEntryNumsOnly:
    for i in range(len(gsWorkingData)):
        if entry in gsWorkingData[i][0]:
        # questioning if this line will be problematic for some test cases...
        # if an entry number appears twice (meaning, if the gold standard isn't perfect and has overlapping entries), i'll need to create a test for the engine output later
            gsDic1[entry] = gsWorkingData[i][1]
    # which looks like {'entry_217' : 'DATE', 'entry_216': 'DATE', 'entry_36': 'DATE', 'entry_274': 'LAST_NAME' ...}

contentNodes = parsedGSDoc.getElementsByTagName('content')
for node in contentNodes:
    text = node.childNodes
    for node in text:
        if node.parentNode.getAttribute('ID') in gsDic1:
            gsDic2[node.parentNode.getAttribute('ID')] = node.data


for entry in gsEntryNumsOnly:
	for i in range(len(gsWorkingData)):
		if entry in gsWorkingData[i][0] and entry in gsDic2:
			finalGSDic[entry] = ((gsWorkingData[i][1], gsDic2[entry]))


##
## Establishing the engine data structures
##

engineCodes = []
engineEntryNumsOnly = []
engineEntryNums = []
engineParent = []

engineCodeNodes = parsedEngineDoc.getElementsByTagName('mm:code')
for node in engineCodeNodes:
    engineCodes.append(node.getAttribute('code'))
    ### codes just looks like a list of all the codes in order of mim appearance ###

engineParent = parsedEngineDoc.getElementsByTagName('mm:binding')
for item in engineParent:
    for child in item.getElementsByTagName('mm:narrativeBinding'):
        engineEntryNumsOnly.append(child.getAttribute('ref'))
        engineEntryNums.append(child.getAttribute('ref'))
    engineEntryNums.append('\n')
del engineEntryNums[-1]

engineEntryNumsGrouped = magicsplit(engineEntryNums, '\n')
engineEntryNumsGroupedTuple = tuple(tuple(x) for x in engineEntryNumsGrouped)
    ### which looks like ((u'entry_102'), (u'entry_7', u'entry_8', u'entry_9'), (u'entry_35', u'entry_36') ...] ###
    ### Helpful because you can see the scoping of a certain mim ... len(entryNumsGrouped[1]) -> 3 (tokens long) ###

engWorkingData = zip(engineEntryNumsGroupedTuple, engineCodes)
engineWorkingData = tuple(engWorkingData)
    ### which looks like [(['entry_102'], 'LAST_NAME'), (['entry_7', 'entry_8', 'entry_9'], 'AGE') ...] ###


##
## Begin comparison of data structures
##

gsSet = set(gsWorkingData)

engineSet = set(engineWorkingData)

#
# True Positives
#
truePositives = list(engineSet.intersection(gsSet))
print "True Positives: (x%s found!)\n" % len(truePositives)
print truePositives

#
# Checking for false positives, false negatives, and mismatches...
#

gsDiffs = gsSet.difference(engineSet)
engineDiffs = engineSet.difference(gsSet)

gsDiffsList = list(gsDiffs)
### What the gold standard said was right ###

engineDiffsList = list(engineDiffs)
### What the engine said was right ###

print "\n\nDifferences in engine versus gold standard:"
print "_____________________________________________\n"

print "In gold standard version but not in engine version (false negatives): (x%s found)" % len(gsDiffs)
print gsDiffs
print ""
print "In engine version but not in gold standard version (false positives): (x%s found)" % len(engineDiffs) 
print engineDiffs
print "\n\n"
### engineDiffs will contain false positives, scopeMismatchValueMatches, and ScopeMatchValueMismatch

#
# Checking for false positives:
#

### defining false positives as just what falls in the above after mismatches are picked out ###

#
# Data structure for mismatches:
#

engineDiffsEntries = []
for i in range(len(engineDiffsList)):
	for j in range(len(engineDiffsList[i][0])):
		engineDiffsEntries.append(engineDiffsList[i][0][j])
print "Engine Diffs Entries"
print engineDiffsEntries

#
# Checking for scope match, value mismatch (Same entry number, different code value):
#

print "\n\nScope Match - Value Mismatch MIMs:\n"

scopeMatchValueMismatch = []
for i in range(len(engineDiffsList)):
    for j in range(len(gsWorkingData)):
        if engineDiffsList[i][0] == gsWorkingData[j][0]:
            print engineDiffsList[i][1] + " was confused for the correct mim code " + gsWorkingData[j][1]
            scopeMatchValueMismatch.append(gsWorkingData[j][0])    

print "x%s mismatch instance(s) of proper scope but incorrect value involving entry number(s):\n" % len(scopeMatchValueMismatch)
print scopeMatchValueMismatch
print "\n\n\n"

outputList = []
documentText = {}

scopeMatchValueMismatchEntryNums = [entryNum for entryNum in scopeMatchValueMismatch]
entryJustNumsList = []
for entry in scopeMatchValueMismatchEntryNums:
    for subentry in entry:
        entryJustNumsList.append(subentry[-3:])

for node in contentNodes:
    text = node.childNodes
    for node in text:
        documentText[node.parentNode.getAttribute('ID')] = node.data

entryNum = entryJustNumsList[0]
for i in range((int(entryNum)-10), (int(entryNum)+10)):
    iterEntryNum = "entry_" + str(i)
    print iterEntryNum
    outputList.append(documentText[iterEntryNum])
                    
outputString = "..." + " ".join(outputList) + "..."
print outputString

# output this as html later with bolded / js tooltip functionality


# Checking for scope mismatch, value match (Overlapping entry numbers, same code value)
#
# Test cases: "in October" vs "October" for DATE, "on October 21 1993" and "October 21 1993" as ABSOLUTE_DATE
# --> entry is in tuple but engine result tuple and gs tuple are different lengths

print "\n\nScope Mismatch - Value Match MIMs:\n"

scopeMismatchValueMatch = []
for i in range(len(gsWorkingData)):
    for j in range(len(engineDiffsList)):
        for k in range(len(engineDiffsList[j][0])):
            if engineDiffsList[j][0][k] in gsWorkingData[i][0] and engineDiffsList[j] not in scopeMismatchValueMatch:
                #want to be checking if scope are same / diff using the truePos list too
                scopeMismatchValueMatch.append(engineDiffsList[j]);

print "Scoping was problematic involving %s MIMs, which were:" % len(scopeMismatchValueMatch)
print scopeMismatchValueMatch

##print '\nConfusion matrix successfully generated.'
##print '\nAll files successfuly written to ' + gsPath

print 'Took', datetime.datetime.now()-startTime, 'to run files.'


## Wikipedia confusion table code
def confusion_table(cfm, label):
    """Returns a confusion table in the following format:
    [[true positives, false negatives],
     [false positives, true negatives]]
    for the given label index in the confusion matrix.
    """
    predicted = cfm[label]
    actual    = [cfm[i][label] for i in range(len(cfm))]
    true_pos  = predicted[label]
    false_pos = sum(actual) - true_pos
    false_neg = sum(predicted) - true_pos
    total     = sum([sum(i) for i in cfm])
    true_neg  = total - true_pos - false_pos - false_neg
 
    return [[true_pos, false_neg],
            [false_pos, true_neg]]



#
# HTML Output
#

with open(os.path.join(path, 'confusionMatrixForDeid.html'), 'w') as out:
    out.write("""<html>
                    <head>
                        <link rel="stylesheet" type="text/css" href="deid.css">
                        <title>Deid Stats Results</title>
                    </head>
                    <body style="font-family:sans-serif">
                        <table>
                            <tr>
                                <td>
                                <h2>Deid Stats Results</h2>""")
    
    out.write('<h4>Generated at: ' + str(datetime.datetime.now()).split('.')[0] + '</h4>')

    out.write('<h3>Total correct: ' + str(len(truePositives)) + '</h3>')
    out.write('<h3>Total errors: ' + str(len(engineDiffsList)) + ' </h3>')
    out.write('<h3>Total GS MIMs: ' + str(len(gsWorkingData)) + '</h3>')
    out.write('<h3>Total Engine MIMs: ' + str(len(engineWorkingData)) + '</h3></td></tr></table>')

    ### just testing for now, but will do this in js later

    out.write("""       <table>
                            <tr>
                                <td></td>
                                <td></td>
                                <th colspan="1" style="border:1px solid black">Predicted (eng)<p><img src="http://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/U%2B2192.svg/25px-U%2B2192.svg.png"></p></th>
                                <td></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td></td>
                                <th style="width:60px;">
                                    <div class="vertical-text">
                                        <div class="vertical-text__inner">Actual (gs)<p><img src="http://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/U%2B2190.svg/25px-U%2B2190.svg.png"></p></div>
                                    </div>
                                </th>
                                <td style="border:1px solid black">DATE</td>
                                <td style="border:1px solid black">HOSPITAL</td>
                                <td style="border:1px solid black">INITIAL</td>
                                <td style="border:1px solid black">LAST_NAME</td>
                                <td style="border:1px solid black">ORG</td>
                                <td style="border:1px solid black">MALE_NAME</td>
                                <td style="border:1px solid black">FEM_NAME</td>
                                <td style="border:1px solid black">LOCATION</td>
                                <td style="border:1px solid black">ABS_DATE</td>
                                <td style="border:1px solid black">PH_NUMBER</td>
                                <td style="border:1px solid black">ADDRESS</td>
                                <td style="border:1px solid black">AGE</td>
                                <td style="border:1px solid black">TIME</td>
                                <td style="border:1px solid black">NAME</td>
                                <td style="border:1px solid black">SSN</td>
                                <td style="border:1px solid black">MRN</td>
                                <td style="border:1px solid black">URL</td>
                                <td style="border:1px solid black">CERTIF_OR</td>
                                <td style="border:1px solid black">ID_OR</td>
                                <td style="border:1px solid black">OTHER</td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">DATE</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">HOSPITAL</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">INITIAL</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">ORGANIZATION</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">LAST_NAME</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">MALE_NAME</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">FEMALE_NAME</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">LOCATION</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">ABSOLUTE_DATE</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">ADDRESS</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">PHONE_NUMBER</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">AGE</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">TIME</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">NAME</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">SSN</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">MRN</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">URL</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">CERTIF_OR</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">ID_OR</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                            <tr style="border:1px solid black">
                                <td style="border:1px solid black">OTHER</td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                                <td style="border:1px solid black"></td>
                            </tr>
                        </table>
                    </div>
                </body>
            </html> """)
    


###'D': ['LAST_NAME', 'MALE_NAME', 'FEMALE_NAME', 'PHONE_NUMBER', 'MEDICAL_RECORD_NUMBER', 'ABSOLUTE_DATE', 'DATE', 'ADDRESS', 'LOCATION', 'AGE', 'SOCIAL_SECURITY_NUMBER', 'CERTIFICATE_OR_LICENSE_NUMBER', 'ID_OR_OTHER_CODE', 'NAME', 'ORGANIZATION', 'URL', 'E_MAIL_ADDRESS', 'TIME', 'OTHER'] ###
