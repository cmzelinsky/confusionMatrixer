# -*- coding: utf-8 -*-
## author : Courtney Zelinsky
## created : 5/13/14
##
## Call on cmd line with arg[1] = gs, arg[2] = engine output for comparison to create a Confusion Matrix
##
## Henry's wishlist:
## "There were 2 minor warts I know of in the code.  
## 1)	It's insufficiently clear if columns are the gold or test set.
## 2)	There is no link from confusion matrix to details files."
##

import datetime, os, xml.dom.minidom, datetime, operator, pickle, sys, libxml2, collections
from xml.dom.minidom import parse
import xml.dom.minidom as minidom
import xml.etree.ElementTree
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element, tostring, SubElement, XML


startTime = datetime.datetime.now()
##args = sys.argv
path = "C:/Users/courtney.zelinsky/Desktop/deid"

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

def findPair(fname): 
    return fname[:-3] + 'out.xml'

def getTextForKWIC(fname, entries):
    '''Intake a nested dict of {filename:{gsLabel:{engineLabel:entryNums, ...}, ...} ...}

    '''
    entries = entries.split(', ')
    doc = minidom.parse(path + '\\' + fname)
    docTemp = ET.parse(path + '\\' + fname)
    concept = []
    text = []
    separator = '::::'
    for entry in entries:
        concept.append(docTemp.find('//content[@ID="' + entry + '"]', doc)[0].firstChild.nodeValue)
    concept = ''.join(concept)[:-1]
    for w in docTemp.find('//paragraph[.//content[@ID="' + entries[0] + '"]]', doc)[0].getElementsByTagName('content'):
        if w.getAttribute('ID') in entries:
            if not w.firstChild.localName == 'hit':
                para.append('<font style="background-color:yellow"><strong>' + w.firstChild.nodeValue + '</strong></font>')
            else:
                para.append('<font style="background-color:yellow"><strong>' + w.firstChild.firstChild.nodeValue + '</strong></font>')
        else:
            if not w.firstChild.localName == 'hit':
                para.append(w.firstChild.nodeValue)
            else:
                para.append(w.firstChild.firstChild.nodeValue)
    para = '<span onclick="showHide(this)" style="cursor:pointer">Context <span class="plusMinus">[+]</span></span><br><span style="display:none">' + ''.join(text) + '</span>'
    return fname + separator + concept + separator + text

## Begin processing...
docCount=0
docs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml' , os.listdir(path))
allData = {}
truePosCount = 0
falseNegCount = 0
falsePosCount = 0
confusionMatrix = {}


matrixValues = [(u'LAST_NAME',), (u'MALE_NAME',), (u'FEMALE_NAME',), (u'PHONE_NUMBER',), (u'MEDICAL_RECORD_NUMBER',), (u'ABSOLUTE_DATE',), (u'DATE',), 
(u'ADDRESS',), (u'LOCATION',), (u'AGE',), (u'SOCIAL_SECURITY_NUMBER',), (u'CERTIFICATE_OR_LICENSE_NUMBER',), (u'ID_OR_OTHER_CODE',), (u'NAME',),
(u'ORGANIZATION',), (u'URL',), (u'E_MAIL_ADDRESS',), (u'TIME',), (u'OTHER',), (u'HOSPITAL',), (u'INITIAL',)]

for doc in docs:
    if not doc.endswith('.out.xml'):
        docCount += 1
        
        print "\n\n_______________________________________\n"
        print "Now parsing document %s out of %s..." % (docCount, len(docs)/2)
        print "_______________________________________\n\n"
        
        parsedGSDoc = parse(path + '\\' + doc)
        parsedEngDoc = parse(findPair(path + '\\' + doc))
        
        gsCodes = []
        gsEntryNumsOnly = []
        gsEntryNums = []
        gsDic2 = {}
        finalGSDic = {}
        gsParent = []
        outputList = []
        documentText = {}
        #engAndGsOnly[doc] = {}

        # Creates rows and columns for the matrix labeled with codes(matrixValues)
        # Instantiates each false/true positive count to 0
        #confusionMatrix[doc] = {}
        for value in matrixValues:
            confusionMatrix[value] = {}
            for value2 in matrixValues:
                confusionMatrix[value][value2] = 0

        def collectText(doc):
            doc = ET.parse(path + '\\' + fname)
            
        
        # Establishing the gold standard data structures
        
        #  assmpt: the gold standard set is perfect & 1:1 
        gsDic = {}
        entries = parsedGSDoc.getElementsByTagName('entry')
        for entry in entries:
            bindings = []
            for child in entry.firstChild.childNodes:
                if child.localName == 'binding':
                    print bindings
                    bindings.extend([narrativeBindings.getAttribute('ref') for narrativeBindings in child.childNodes])
                    entries = tuple(str(binding) for binding in bindings if len(binding)>0)
                    print entries 
                    value = [child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code'] # added if filter here, because why would we need the manual validation codes? 
                    print value
                    if entries in gsDic:
                        gsDic[entries].append(str(value).strip('[]'))
                    else:
                        gsDic[entries] = value
        for k, v in gsDic.items():
            gsDic[k] = tuple(v)
                        
        # if the gold standard isn't perfect + has overlapping entries, it will be seen here but is not yet tested/fixed


##        contentNodes = parsedGSDoc.getElementsByTagName('content')
##        for node in contentNodes:
##            text = node.childNodes
##            for node in text:
##                if node.parentNode.getAttribute('ID') in gsDic1:
##                    gsDic2[node.parentNode.getAttribute('ID')] = node.data
        # {u'entry_202': u'January', u'entry_203': u'2012.', u'entry_303': u"Jude's", u'entry_302': u'St.'...}
        
        ##for entry in gsEntryNumsOnly:
        ##    for i in range(len(gsWorkingData)):
        ##      if entry in gsWorkingData[i][0] and entry in gsDic2:
        ##          finalGSDic[entry] = ((gsWorkingData[i][1], gsDic2[entry]))

        # Don't need this if I can get the xpath module working ^^^
        

        ## Establishing the engine data structures
        engDic = {}
        entries = parsedEngDoc.getElementsByTagName('entry')
        for entry in entries:
            bindings = []
            for child in entry.firstChild.childNodes:
                if child.localName == 'binding':
                    bindings.extend([narrativeBindings.getAttribute('ref') for narrativeBindings in child.childNodes])
                    entries = tuple(str(binding) for binding in bindings if len(binding)>0)
                    value = [child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code'] # added if filter here, because why would we need the manual validation codes? 
                    if entries in engDic:
                        engDic[entries].append(str(value).strip('[]'))
                    else:
                        engDic[entries] = value
        for k, v in engDic.items():
            engDic[k] = tuple(v)

            
        ## Begin comparison of data structures

        # True Positives
        truePositives = {entry:tuple(gsDic[entry]) for entry in gsDic if entry in engDic and gsDic[entry] == engDic[entry]}
        # Add multi-code entries as well:
        for entry in gsDic.keys():
            if entry in gsDic.keys() and entry in engDic.keys() and entry not in truePositives:
                truePositives[entry] = tuple(code for code in gsDic[entry])
            
        # Increments true positive counters in the confusion matrix
        for entry in gsDic.keys():
            if entry in truePositives and truePositives[entry] == gsDic[entry]:
                if truePositives[entry] in confusionMatrix and truePositives[entry] in confusionMatrix[truePositives[entry]]:
                    #if entry in engDic and engDic[entry] == gsDic[entry] # If the value exists, increment it
                   confusionMatrix[truePositives[entry]][truePositives[entry]] += 1
                # If the value doesn't exist, add another row/column for it
                else:
                    confusionMatrix[truePositives[entry]] = {}
                    for value2 in matrixValues:
                        confusionMatrix[truePositives[entry]][value2] = 0
                    confusionMatrix[truePositives[entry]][truePositives[entry]] = 1
        print "True Positives: (x%s found!)\n" % len(truePositives)
        truePosCount += len(truePositives)
        print truePositives
        
        # Checking for false positives, false negatives, and mismatches...

        gsDiffs = {entry:gsDic[entry] for entry in gsDic if entry not in engDic}
        engDiffs = {entry:engDic[entry] for entry in engDic if entry not in gsDic}

##        # Increments false positive count
##        # Checks whether entries that exist in the engine exist in the gold standard
##        # If not, it's a false positive
##        # NOTE: Doesn't include error checking. Basing it off the true positives' error checking
##        for entry in engDic:
##            # If value is in engine and not gs, increment
##            if entry not in gsDic:
##                if "ENGINE_ONLY_ENTRY" in confusionMatrix:
##                    print "x1 engine only entry in confMatrix, so now incrementing"
##                    confusionMatrix["ENGINE_ONLY_ENTRY"][engDic[entry]] += 1
##                else:
##                    print "no engine only entry found for this dic in confmatrix, now making a new dic"
##                    confusionMatrix["ENGINE_ONLY_ENTRY"] = {}
##                    for value in matrixValues:
##                        print "now initializing code from matrixValues to zero"
##                        confusionMatrix["ENGINE_ONLY_ENTRY"][value] = 0
##                    print confusionMatrix["ENGINE_ONLY_ENTRY"]
##                    print "x1 engine only entry created, and now incrementing"
##                    confusionMatrix["ENGINE_ONLY_ENTRY"][engDic[entry]] += 1
##            # If entries exist in both but codes don't match (e.g, DATE =/= ABSOLUTE_DATE), increment false positive count
####            elif gsDic[entry] != engDic[entry]:
####                confusionMatrix[gsDic[entry]][engDic[entry]] += 1
        
##        # Increments false negative count
##        # Checks whether entries that exist in the gold standard exist in the engine
##        # If not, it's a false negative
##        # NOTE: Doesn't include error checking. Base it off the true positives' error checking
##        for entry in gsDic:
##            if entry not in engDic:
##                if "GS_ONLY_ENTRY" in confusionMatrix[gsDic[entry]]:
##                    confusionMatrix[gsDic[entry]]["GS_ONLY_ENTRY"] += 1
##                else:
##                    confusionMatrix[gsDic[entry]]["GS_ONLY_ENTRY"] = 1

        ### gsDiffs = What the gold standard said was right ###
        ### engineDiffs = What the engine said was right ###

        print "\n\nDifferences in engine versus gold standard:"
        print "_____________________________________________\n"
        print "In gold standard version but not in engine version (false negatives): (x%s found)" % len(gsDiffs)
        falseNegCount += len(gsDiffs)
        print gsDiffs
        print ""
        print "In engine version but not in gold standard version (false positives): (x%s found)" % len(engDiffs)
        falsePosCount += len(engDiffs)
        print engDiffs
        print "\n\n"
        ### engineDiffs will contain false positives, scopeMismatchValueMatches, and ScopeMatchValueMismatch
        
        # Checking for false positives:
        #  defining false positives as just what falls in the above after mismatches are picked out ###
        gsDiffsEntries = gsDiffs.keys()
        engineDiffsEntries = engDiffs.keys()
        engDiffsEntries = engineDiffsEntries
        
        # Checking for scope match, value mismatch (Same entry number, different code value):
        print "\n\nScope Match - Value Mismatch MIMs:"
        print "_____________________________________________\n"

        scopeMatchValueMismatch = []
        """
        print("~")
        print(engineDiffsEntries)
        print("-----")
        print(gsDic)
        print("-------")
        print(gsDiffsEntries)
        print("~")
        for i in range(len(engDiffsEntries)):
            for j in range(len(gsDic)):
            # Comparing against true positives
                if engDiffsEntries[i] == gsDic.keys()[j][0]:
                # in other words, if the scopes (read: the tuple of entry numbers) are the same, then...
                    print engineDiffsEntries[i][1] + " was confused for the correct mim code " + gsDic[gsDic.keys()[j]]
                    scopeMatchValueMismatch.append(gsDic[j][0])
        """
        # Get each gs diff entry (ede -- engine diff entry)
        for gde in gsDiffsEntries:
            # Get the key (a tuple) of each gold standard dic item
            for key in gsDic.keys():
                # Convert each to a string for easy comparison
                strGDE = str(gde)
                strKey = str(key)
                if strGDE == strKey:
                    print("same")

        # Checking for overlap

##        print("************\nOverlap handling\n")
##        incompleteOverlaps = 0
##        completeOverlaps = 0
##        for gsKeyTup in gsDic.keys():
##            for i in range(len(gsKeyTup)):
##                for engKeyTup in engDic.keys():
##                    for j in range(len(engKeyTup)):
##                        # If any value within the gsKey's tuple overlaps with the engineKey's tuple, count it as an overlap
##                        if str(gsKeyTup[i]) == str(engKeyTup[j]):
##                            if str(gsKeyTup) == str(engKeyTup):
##                                completeOverlaps += 1
##                                print str(gsKeyTup)
##                                print str(engKeyTup)
##                                print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" + str(engKeyTup[j]) + " " + str(engKeyTup) + "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
##                            else:
##                                incompleteOverlaps += 1
##                    if completeOverlaps > 0 or incompleteOverlaps > 0:
##                        print str(gsKeyTup) + " : " + str(engKeyTup)
##                        print str(gsDic[gsKeyTup]) + " : " + str(engDic[engKeyTup])
##                        print("/////////////////////")
##                        break
##                if incompleteOverlaps > 0 or completeOverlaps > 0:
##                    break

        print "x%s mismatch instance(s) of proper scope but incorrect value involving entry number(s):\n" % len(scopeMatchValueMismatch)
        print scopeMatchValueMismatch
        print "\n"
        scopeMatchValueMismatchEntryNums = [entryNum for entryNum in scopeMatchValueMismatch]
        entryJustNumsList = []
        for entry in scopeMatchValueMismatchEntryNums:
            for subentry in entry:
                entryJustNumsList.append(subentry.split("_")[1])

        # Checking for scope mismatch, value match (Overlapping entry numbers, same code value)
        #
        # Test cases: "in October" vs "October" for DATE, "on October 21 1993" and "October 21 1993" as ABSOLUTE_DATE
        # --> entry is in tuple but engine result tuple and gs tuple are different lengths
        engDiffsEntries = {}
        print "\n\nScope Mismatch - Value Match MIMs:"
        print "_____________________________________________\n"
        scopeMismatchValueMatch = []


##        for i in range(len(gsWorkingData)):
##            for j in range(len(engineDiffsList)):
##                for k in range(len(engineDiffsList[j][0])):
##                    if engineDiffsList[j][0][k] in gsWorkingData[i][0] and engineDiffsList[j] not in scopeMismatchValueMatch:
##                        #want to be checking if scope are same / diff using the truePos list too
##                        scopeMismatchValueMatch.append(engineDiffsList[j]);
##        print "Scoping was problematic involving %s MIMs, which were:" % len(scopeMismatchValueMatch)
##        print scopeMismatchValueMatch
        



print 'Totals'
print 'True Positives: ' + str(truePosCount)
print 'False Negatives: ' + str(falseNegCount)
print 'False Positives: ' + str(falsePosCount)


#
# HTML Output
#

#vals = ['LAST_NAME', 'MALE_NAME', 'FEMALE_NAME', 'PHONE_NUMBER', 'MEDICAL_RECORD_NUMBER', 'ABSOLUTE_DATE', 'DATE',
#        'ADDRESS', 'LOCATION', 'AGE', 'SOCIAL_SECURITY_NUMBER', 'CERTIFICATE_OR_LICENSE_NUMBER', 'ID_OR_OTHER_CODE',
#        'NAME', 'ORGANIZATION', 'URL', 'E_MAIL_ADDRESS', 'TIME', 'OTHER']
 

##    out.write('<h3>Total correct: ' + str(len(truePositives)) + '</h3>')
##    out.write('<h3>Total errors: ' + str(falsePosCount+falseNegCount) + ' </h3>')
##    out.write('<h3>Total GS MIMs: ' + str(len(gsDic)) + '</h3>')
##    out.write('<h3>Total Engine MIMs: ' + str(len(engDic)) + '</h3></td></tr></table>')


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class TElement(ET._Element):
    
    def __init__(self, tag, style=None, text=None, tail=None, parent=None, attrib={}, **extra):
        ET._Element.__init__(self, tag, dict(attrib, **extra))
        
        if text:
            self.text = text
        if tail:
            self.tail = tail
        if style:
            self.style = style
        if not parent == None:
            parent.append(self)
            
# Creating dom structure, adding proper headers and td's for each label of comparison

root = TElement('root')

html = TElement('html', parent=root)

#Header
head = TElement('head', parent=html)

title = TElement('title', text="Deid Stats Results", parent=head)
css = TElement('link', parent=head)

css.attrib['href'] = "css.css"
css.attrib['type'] = "text/css"
css.attrib['rel'] = "stylesheet"

head.extend(css)
head.extend(title)

#Body

values = sorted([key for key in confusionMatrix.keys()])


body = TElement('body', parent=html)

h1 = TElement('h1', text="Deid Stats Results:", parent=body)

timeGenerated = TElement('p', text="Generated at: " + str(datetime.datetime.now()).split('.')[0], parent=body)

table = TElement('table', parent=body)

headerRow = TElement('tr', parent=table)

tableHeaders = [ TElement('th', text=column[0]) for column in values]

headerRow.extend(TElement('th', parent=headerRow))
headerRow.extend(TElement('th', text="Engine:", parent=headerRow))
headerRow.extend(tableHeaders)

goldBlankRow = TElement('tr', parent=table)
goldBlankRow.extend(TElement('th', text="Gold Standards:", parent=goldBlankRow))

tdList = []
for column in values:
    dataRow = TElement('tr', parent=table)
    rowHeader = TElement('th', text=column[0], parent=dataRow)
    blankData = TElement('td', parent=dataRow)
    for row in values:
        #getting the td data for each row in pulling from the confusionMatrix dic
        comparisonData = [TElement('td', text=str(confusionMatrix[column][row])) for row in values]
        for tdElement in comparisonData:
            if tdElement.text != '0':
                tdElement.attrib['style'] = "background:orange"
            dataRow.extend(tdElement)
    dataRow.extend(rowHeader)
    dataRow.extend(blankData)
    dataRow.extend(comparisonData)


authorship = TElement('p', text="Email courtney.zelinsky@mmodal.com for questions / comments / suggestions for this script", parent=body)


# KWIC examination text to go here in html

# for the file it's hashed to, if some entry numbers appeared in false positives or false negatives, get all text descendents from paragraph nodes 

with open(os.path.join(path, "confusionMatrix-Deid.html"), 'w') as outputFile:
    for i in range(len(root)):
        outputFile.write(ET.tostring(root[i]))
outputFile.close()

print '\nConfusion Matrix generated -- written to ' + path
print 'Took', datetime.datetime.now()-startTime, 'to run', len(docs)/2, 'file(s).'
