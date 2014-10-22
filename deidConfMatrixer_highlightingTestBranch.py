# -*- coding: utf-8 -*-
## author : Courtney Zelinsky
## created : 5/13/14
##
## Call on cmd line with arg[1] = path containing all files for testing, gs files in the format ~.xml and their engine counterparts ~.out.xml
##
## Wishlist:
## "There were 2 minor warts I know of in the code.  
## 1)	It's insufficiently clear if columns are the gold or test set.  [Check]
## 2)	There is no link from confusion matrix to details files."       [Check]
##

import datetime, os, xml.dom.minidom, datetime, sys, re, time
from xml.dom.minidom import parse
import xml.dom.minidom as minidom
import xml.etree.ElementTree
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, tostring, SubElement, XML, XMLParser
from lxml import etree


startTime = datetime.datetime.now()
#path = sys.argv[1]
path = "C:/Users/courtney.zelinsky/Desktop/beta"

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

def findPair(fname): 
    return fname[:-3] + 'out.xml'

def appendKWIC():
    contextNode = Doc.createElement('ul')
    docNode = Doc.createElement('h3')
    docText = Doc.createTextNode(docName)
    docNode.appendChild(docText)
    contextNode.appendChild(docNode)
    for snippet in snippets:
        print "before: ", snippet
        snippet = "<p>" + re.sub('&', '', snippet.encode('ascii', 'replace')) + "</p>"
        print "\nafter: " + snippet
        parsedSnippet = minidom.parseString(snippet).firstChild
        print "parsedSnippet: ", parsedSnippet
        contextNode.appendChild(parsedSnippet)
    print contextNode.toxml(), " getting appended to contextsTable"
    contextsTable.appendChild(contextNode)

#truePositivesMaster = {"B~ClinicalDocument_2531456463.xml":{('entry_60', 'entry_61'): (u'ABSOLUTE_DATE',), ('entry_201', 'entry_202'): (u'ABSOLUTE_DATE',), ('entry_185', 'entry_186'): (u'ABSOLUTE_DATE',), ('entry_235', 'entry_236'): (u'ABSOLUTE_DATE',), ('entry_20', 'entry_21'): (u'ABSOLUTE_DATE',), ('entry_282',): (u'LAST_NAME',), ('entry_144', 'entry_145'): (u'ABSOLUTE_DATE',), ('entry_18', 'entry_19'): (u'ABSOLUTE_DATE',), ('entry_140', 'entry_141'): (u'ABSOLUTE_DATE',), ('entry_244', 'entry_245'): (u'ABSOLUTE_DATE',), ('entry_566',): (u'LOCATION',), ('entry_216', 'entry_217'): (u'ABSOLUTE_DATE',), ('entry_13', 'entry_14', 'entry_15'): (u'ABSOLUTE_DATE',), ('entry_85', 'entry_86'): (u'ABSOLUTE_DATE',), ('entry_131', 'entry_132'): (u'ABSOLUTE_DATE',), ('entry_256', 'entry_257'): (u'ABSOLUTE_DATE',), ('entry_388',): (u'LAST_NAME',), ('entry_8',): (u'LAST_NAME',), ('entry_271', 'entry_272'): (u'ABSOLUTE_DATE',), ('entry_7',): (u'FEMALE_NAME',), ('entry_228', 'entry_229'): (u'ABSOLUTE_DATE',), ('entry_70', 'entry_71'): (u'ABSOLUTE_DATE',), ('entry_285',): (u'AGE',), ('entry_103', 'entry_104'): (u'ABSOLUTE_DATE',)}}
#just using truePositives for testing here, but this will be the format when an error dictionary is established
#Need FP and FN from each doc, preferably in format {doc:{FP:{entry:code, entry:code, ...}, FN:{entry:code, entry:code}}}

class TElement(ET._Element):
    """Extending elementtree's Element class so as to accommodate text"""
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

## Begin processing...
docCount=0
# Filter only xml files as the file type to be tested
docs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml' , os.listdir(path))

# Labels to be tested -- implement later as a dictionary later so as to accommodate Certainty, Temporality, Subject, Acuity, etc.
matrixValues = [(u'LAST_NAME',), (u'MALE_NAME',), (u'FEMALE_NAME',), (u'PHONE_NUMBER',), (u'MEDICAL_RECORD_NUMBER',), (u'ABSOLUTE_DATE',), (u'DATE',), 
(u'ADDRESS',), (u'LOCATION',), (u'AGE',), (u'SOCIAL_SECURITY_NUMBER',), (u'CERTIFICATE_OR_LICENSE_NUMBER',), (u'ID_OR_CODE_NUMBER',), (u'NAME',),
(u'ORGANIZATION',), (u'URL',), (u'E_MAIL_ADDRESS',), (u'TIME',), (u'OTHER',), (u'HOSPITAL',), (u'INITIAL',), (u'HOSPITAL_SUB',)]

allData = {}
truePosCount = 0
falseNegCount = 0
falsePosCount = 0
confusionMatrix = {}
incompOverlaps = {}
compOverlaps = {}
finalIncompOverlaps = {}
truePosFromOverlaps = {}
truePosWithOverlaps = {}
diffsDic = {}
overlapsForKWIC = {}

#for engine only or gs only MIMs
# will be used in referencing FN and FP (for MIMs occuring only in the engine) counts in the matrix table rendering below
fnDic = {}
for value in matrixValues:
    fnDic[value] = 0

fpDic = {}
for value in matrixValues:
    fpDic[value] = 0

errors = {}
truePositives = {}
gsDic = {}
engDic = {}


for doc in docs:
    if not doc.endswith('.out.xml'):
        docCount += 1
        #for x in xrange(0, len(docs)/2):
        #percent = float(x) / (len(docs)/2)
        #hashes = '#' * int(round(percent * 20))
        #spaces = ' ' * (20 - len(hashes))
        sys.stdout.write("\r_______________________________________\n\nNow running document %s out of %s...\n_______________________________________\n" % (docCount, len(docs)/2))
        sys.stdout.flush()
        parsedGSDoc = parse(path + '\\' + doc)
        parsedEngDoc = parse(findPair(path + '\\' + doc))
        
        outputList = []
        documentText = {}
                
        # Creates rows and columns for the matrix labeled with codes(matrixValues)
        # Instantiates each false/true positive count to 0
        confusionMatrix[doc] = {}
        for value in matrixValues:
            confusionMatrix[doc][value] = {}
            for value2 in matrixValues:
                confusionMatrix[doc][value][value2] = 0
        
        # Establishing the gold standard data structures
        
        #  assmpt: the gold standard set is perfect & 1:1 
        gsDic[doc] = {}
        entries = parsedGSDoc.getElementsByTagName('entry')
        for entry in entries:
            bindings = []
            for child in entry.firstChild.childNodes:
                if child.localName == 'binding':
                    bindings.extend([bindingNode.getAttribute('ref') for bindingNode in child.childNodes if bindingNode.localName == "narrativeBinding"])
                    entries = tuple(sorted(str(binding) for binding in bindings if len(binding)>0))
                    value = [child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code'] # added if filter here, because why would we need the manual validation codes? 
                    if len(entries) == 0:
                        #takes out nodes without text which are generated from section header MIMs
                        print "CONTINUING"
                        continue
                    else:
                        gsDic[doc][entries] = value
        for k, v in gsDic[doc].items():
            gsDic[doc][k] = tuple(v)
            #print "gs dic: ", k, tuple(v)
                        
        # if the gold standard isn't perfect + has overlapping entries, it will be seen here but is not yet tested/fixed
        # --> Create alert that funnels gs documents having overlapping MIMs and output at end of script
        
        ## Establishing the engine data structures
        engDic[doc] = {}
        entries = parsedEngDoc.getElementsByTagName('entry')
        for entry in entries:
            bindings = []
            for child in entry.firstChild.childNodes:
                
                if child.localName == 'binding':
                    bindings.extend([bindingNode.getAttribute('ref') for bindingNode in child.childNodes if bindingNode.localName == "narrativeBinding"])
                    entries = tuple(sorted(str(binding) for binding in bindings if len(binding)>0))
                    value = [child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code'] # added if filter here, because why would we need the manual validation codes? 
                    if len(entries) == 0:
                        print "CONTINUING"
                        continue
                    elif entries in engDic[doc]:
                        engDic[doc][entries].append("".join(value))
                    elif entries not in engDic[doc]:
                        engDic[doc][entries] = value
        for k, v in engDic[doc].items():
            engDic[doc][k] = tuple(v)
            #print "eng dic: ", k, tuple(v)
         
        ## Begin comparison of data structures

        # True Positives
        truePositives[doc] = {entry:tuple(gsDic[doc][entry]) for entry in gsDic[doc] if (entry in engDic[doc] and gsDic[doc][entry] == engDic[doc][entry])}
        # Handle multi-code entries as well, for instance gs: (entry_7,): (u'AGE'), eng: (entry_7,): (u'AGE', u'AGE') -kind of overlapping:
        for entry in gsDic[doc].keys():
            if entry in gsDic[doc].keys() and entry in engDic[doc].keys() and entry not in truePositives[doc]:
                truePositives[doc][entry] = tuple(code for code in gsDic[doc][entry])
            
        # Increments true positive counters in the confusion matrix
        for entry in gsDic[doc].keys():
            if entry in truePositives[doc] and truePositives[doc][entry] == tuple(gsDic[doc][entry]):
                if truePositives[doc][entry] in confusionMatrix[doc] and truePositives[doc][entry] in confusionMatrix[doc][truePositives[doc][entry]]:
                    #if entry in engDic and engDic[entry] == gsDic[entry] # If the value exists, increment it
                   confusionMatrix[doc][truePositives[doc][entry]][truePositives[doc][entry]] += 1
                # If the value doesn't exist, add another row/column for it
                else:
                    confusionMatrix[doc][truePositives[doc][entry]] = {}
                    for value2 in matrixValues:
                        confusionMatrix[doc][truePositives[doc][entry]][value2] = 0
                    confusionMatrix[doc][truePositives[doc][entry]][truePositives[doc][entry]] = 1
        #print "\n\nTrue Positives: (x%s found!)\n" % len(truePositives[doc])
        truePosCount += len(truePositives[doc])
        #print truePositives[doc]
        
        # Checking for false positives, false negatives, and mismatches...

        #False negatives:
        gsDiffs = {entry:gsDic[doc][entry] for entry in gsDic[doc] if entry not in engDic[doc]}
        #All entries that are not exactly so in the engine output as they are in the gold standard
        
        #False positives: 
        engDiffs = {entry:engDic[doc][entry] for entry in engDic[doc] if ((entry not in gsDic[doc]) or (entry in gsDic[doc] and gsDic[doc][entry] != engDic[doc][entry]))}
        #including each kind of fp -- 1) FPs that aren't in the gold standard (e.g. "He" as a last name).
        # 2) FPs that are in the gold standard but don't have the same code (e.g. what's in the matrix table).

        diffsDic[doc] = {}
        diffsDic[doc]['FP'] = engDiffs
        diffsDic[doc]['FN'] = gsDiffs

        errors[doc] = {}
        
        engDiffsOneToOne = {}
        for entry in engDiffs:
            if len(entry) > 1:
                for subentry in entry:
                    engDiffsOneToOne[(subentry,)] = engDiffs[entry]
            else:
                engDiffsOneToOne[entry] = engDiffs[entry]

        errors[doc]["FP"] = {}
        errors[doc]["FP"] = engDiffsOneToOne

        gsDiffsOneToOne = {}
        for entry in gsDiffs:
            if len(entry) > 1:
                for subentry in entry:
                    gsDiffsOneToOne[(subentry,)] = gsDiffs[entry]
            else:
                gsDiffsOneToOne[entry] = gsDiffs[entry]

        errors[doc]["FN"] = {}
        errors[doc]["FN"] = gsDiffsOneToOne

        # Increments false positive count
        # Checks whether entries that exist in the engine exist in the gold standard
        # If not, it's a false positive
        # NOTE: Doesn't include error checking. Basing it off the true positives' error checking
        for entry in engDic[doc]:
            # If value is in engine and not gs, increment
            if entry not in gsDic[doc]:
                if len(engDic[doc][entry]) > 1:
                    # check KeyError: (u'FEMALE_NAME', u'DATE') for doc 47/313 (probably 'B~ClinicalDocument_2531473614.xml')
                    for code in engDic[doc][entry]:
                        fpDic[(code,)] += 1
                else: fpDic[engDic[doc][entry]] += 1
##                if "ENGINE_ONLY_FP" in errorDic[doc]:
##                    print "x1 engine only entry in confMatrix, so now incrementing"
##                    errorDic[doc]["ENGINE_ONLY_FP"][engDic[doc][entry]] += 1
##                else:
##                    #no engine only entry found for this dic in confmatrix, making a new dic
##                    errorDic[doc]["ENGINE_ONLY_FP"] = {}
##                    for value in matrixValues:
##                        #initialize code from matrixValues to zero"
##                        errorDic[doc]["ENGINE_ONLY_FP"][value] = 0
##                    errorDic[doc]["ENGINE_ONLY_FP"][engDic[doc][entry]] += 1
            # Non-matching codes handling
            else:
                #if the entry numbers exist in both but the engineDic has a multi-code entry (meaning, overlapping MIMs)
                if len(engDic[doc][entry]) > 1:
                    for code in engDic[doc][entry]:
                        #print "code that is in engDic[doc][entry]: ", code
                        if code not in gsDic[doc][entry]:
                            #print "code that is not in gsDic[doc][entry]: ", code
                            confusionMatrix[doc][gsDic[doc][entry]][(code,)] += 1
                # Otherwise, entries exist in both but codes don't match (e.g, DATE =/= ABSOLUTE_DATE), increment false positive count
                elif gsDic[doc][entry] != engDic[doc][entry]:
                    confusionMatrix[doc][gsDic[doc][entry]][engDic[doc][entry]] += 1
        
        # Increments false negative count
        # Checks whether entries that exist in the gold standard exist in the engine
        # If not, it's a false negative
        # NOTE: Doesn't include error checking. Base it off the true positives' error checking
        for entry in gsDic[doc]:
            if entry not in engDic[doc]:
                fnDic[gsDic[doc][entry]] += 1
                #print "initialized a false negative entry"

        ### gsDiffs = What the gold standard said was right ###
        ### engineDiffs = What the engine said was right ###

        falseNegCount += len(gsDiffs)
        falsePosCount += len(engDiffs)
        ### engineDiffs will contain false positives, scopeMismatchValueMatches, and ScopeMatchValueMismatch
        
        gsDiffsEntries = gsDiffs.keys()
        engineDiffsEntries = engDiffs.keys()
        engDiffsEntries = engineDiffsEntries
        
        # GS Diffs = False negatives...             
        # Get each gs diff entry (ede -- engine diff entry)
##        for entry in gsDiffsEntries:
##            # Get the key (a tuple) of each gold standard dic item
##            for key in gsDic[doc].keys():
##                # Convert each to a string for easy comparison
##                strGDE = str(entry)
##                strKey = str(key)
##                if strGDE == strKey:
                    #print("same")
        
        # Checking for overlap
        overlapsForKWIC[doc] = []
        incompOverlaps[doc] = {}
        compOverlaps[doc] = {}
        finalIncompOverlaps[doc] = {}
        incompleteOverlaps = 0
        completeOverlaps = 0
        for gsKeyTup in gsDic[doc].keys():
            for i in range(len(gsKeyTup)):
                for engKeyTup in engDic[doc].keys():
                    for j in range(len(engKeyTup)):
                        # If any value within the gsKey's tuple overlaps with the engineKey's tuple, count it as an overlap
                        if str(gsKeyTup[i]) == str(engKeyTup[j]):   #if one token from each gs and eng tuples are the same
                            #verifying codes are equal
                            #if gsDic[doc][gsKeyTup] == engDic[doc][engKeyTup]: #if codes are the same 
                            if str(gsKeyTup) == str(engKeyTup): 
                                #adding entry tuple and code to the complete overlaps dictionary so as to get tossed into the KWIC function later
                                compOverlaps[doc][gsKeyTup] = engDic[doc][engKeyTup]
                            else:
                                incompOverlaps[doc][gsKeyTup] = engKeyTup
                                #overlapsForKWIC[doc].append([gsKeyTup, engKeyTup, set(gsKeyTup).intersection(engKeyTup)])
        #print "complete overlap count: " + str(completeOverlaps)
        #print "incomplete overlap count: " + str(incompleteOverlaps)

        #comparison of engine and gs entry tuples to sort out TP from FP overlaps based on criteria
        if incompOverlaps[doc]:
            for gsTup, engTup in incompOverlaps[doc].items():
                truePosFromOverlaps[doc] = {}
                if len(gsTup) < len(engTup):
                    #print "length of engine tuple: ", len(engTup), " ", engTup, "  length of gs tuple (shorter): ", len(gsTup), " ", gsTup
                    testList = []
                    testList.append('entry_' + str(int(sorted(list(gsTup))[0].split("_")[1])-1))
                    testList.extend(sorted(list(gsTup)))
                    testList.append('entry_' + str(int(sorted(list(gsTup))[-1].split("_")[1])+1))
                    #print "test list " + str(tuple(testList)) + " vs. engTup " + str(engTup)
                    if len(gsTup)*1.0 / len(engTup) >= 3/4:
                        truePosFromOverlaps[doc][engTup] = engDic[doc][engTup]
                    elif len(tuple(testList))*1.0 / len(engTup) >= 2/3:
                        if tuple(sorted(testList)) == tuple(sorted(list(engTup))):
                            #TP!
                            truePosFromOverlaps[doc][engTup] = engDic[doc][engTup]
                        else:
                            #FP...
                            finalIncompOverlaps[doc][engTup] = engDic[doc][engTup]
                    else:
                        finalIncompOverlaps[doc][engTup] = engDic[doc][engTup]
                        
                elif len(engTup) < len(gsTup):
                    #print "length of engine tuple (shorter): ", len(engTup), " ", engTup, "  length of gs tuple: ", len(gsTup), " ", gsTup
                    testList = []
                    testList.append('entry_' + str(int(sorted(list(engTup))[0].split("_")[1])-1))
                    testList.extend(sorted(list(engTup)))
                    testList.append('entry_' + str(int(sorted(list(engTup))[-1].split("_")[1])+1))
                    #print "test list " + str(testList) + " vs. gsTup " + str(gsTup)
                    if len(engTup)*1.0 / len(gsTup) >= 3/4: #75% match condition
                        truePosFromOverlaps[doc][engTup] = engDic[doc][engTup]
                    elif len(tuple(testList))*1.0 / len(gsTup) >= 2/3: #this and next 'if' statement being the "plus or minus one token on either side" condition
                        if tuple(sorted(testList)) == tuple(sorted(list(gsTup))):
                            #TP!
                            truePosFromOverlaps[doc][engTup] = engDic[doc][engTup]
                        else:
                            #FP...
                            finalIncompOverlaps[doc][engTup] = engDic[doc][engTup]
                    else:
                        finalIncompOverlaps[doc][engTup] = engDic[doc][engTup]

            #want to compbine the true positives and the overlap-derived true positives so as to retake statistics on these separately
            #this method below is wrong though -- need to put any additional overlaps in the same document.
            
            truePosWithOverlaps[doc] = {}
            truePosWithOverlaps[doc] = dict(truePosFromOverlaps[doc].items() + truePositives[doc].items())

            #sys.stdout.write("\rPercent: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
            #sys.stdout.flush()
            
        
        finalData = {}
        # initialize final data with 0-counts
        for value in matrixValues:
            finalData[value] = {}
            for value2 in matrixValues:
                    finalData[value][value2] = 0
                    
        # summing totals for each gsKey
        for doc in confusionMatrix:
            for key in confusionMatrix[doc]:
                for secondKey in confusionMatrix[doc][key]:
                    if key in finalData and secondKey in finalData[key]:
                        finalData[key][secondKey] += confusionMatrix[doc][key][secondKey]

# Final Report

print '\nTotals'
print 'True Positives: ' + str(truePosCount)
print 'False Negatives: ' + str(falseNegCount)
print 'False Positives: ' + str(falsePosCount)

print 'Precision (TP/TP+FP): ' + str(float(truePosCount)/float(truePosCount+falsePosCount))
print 'Recall (TP/TP+FN): ' + str(float(truePosCount)/float(truePosCount+falseNegCount))

#
# HTML Output
#

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

jquery = TElement('script', text="//", parent=head)
jquery.attrib['src'] = "http://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"

head.extend(css)
head.extend(title)
head.extend(jquery)

#Body

values = sorted([key for key in finalData.keys()])

body = TElement('body', parent=html)

h1 = TElement('h1', text="Deid Stats Results:", parent=body)

timeGenerated = TElement('p', text="Generated at: " + str(datetime.datetime.now()).split('.')[0], parent=body)

table = TElement('table', parent=body)
table.attrib['class'] = "ellipsable"

headerRow = TElement('tr', parent=table)

blankTableHeader = TElement('th', parent=headerRow)
blankTableHeader.attrib['class'] = "blank"
headerRow.extend(blankTableHeader)

#adding all test labels and stats labels as headers for the matrix table
engineHeader = TElement('th', text="Engine:", parent=headerRow)
engineHeader.attrib['style'] = "background: #0962ac;"
tableHeaders = [ TElement('th', text=column[0], attrib={'title':column[0]}) for column in values]
tableHeaders.append(TElement('th', text="FNs", attrib={'style':'background:#0962ac'}))
tableHeaders.append(TElement('th', text="Tp+Fp", attrib={'style':'background:#0962ac;'}))
tableHeaders.append(TElement('th', text="Fscore", attrib={'style':'background:#0962ac;'}))
tableHeaders.append(TElement('th', text="mRecall", attrib={'style':'background:#0962ac'}))
tableHeaders.append(TElement('th', text='mPrecision', attrib={'style':'background:#0962ac;'}))
for th in tableHeaders:
    th.attrib['class'] = "resizable"
headerRow.extend(engineHeader)
headerRow.extend(tableHeaders)
goldBlankRow = TElement('tr', parent=table)
goldHeader = TElement('th', text="Golds:", parent=goldBlankRow)
goldHeader.attrib['style'] = "background: #0962ac;"
goldBlankRow.extend(goldHeader)

#for each test label:
for column in values:
    counter = 0
    tp = 0
    fp = 0
    dataRow = TElement('tr', parent=table)
    rowHeader = TElement('th', text=column[0], parent=dataRow, attrib={'title':column[0]})
    blankData = TElement('td', parent=dataRow)
    blankData.attrib['style'] = "border:0px"
    blankData.attrib['class'] = "BLANK"
    comparisonData = []
    fn = fnDic[column]
    comparisonData.extend([TElement('td', text=str(finalData[column][row]), attrib={'column':row[0]}) for row in values])
    #print "fn ", fn, " for row ", row
    for tdElement in comparisonData:
        tdElement.attrib['row'] = column[0] #[0] for getting the string inside the tuples 
        if not 'style' in tdElement.attrib and tdElement.attrib['column'] == tdElement.attrib['row']:
            tp = int(tdElement.text)
            tdElement.attrib['style'] = "background: #00cd00; border: 1px solid #404040; color: yellow; font-weight:bold;"
        elif tdElement.text != '0' and tdElement.attrib['column'] != tdElement.attrib['row'] and not tdElement.text == None:
            fp += int(tdElement.text)
            tdElement.attrib['style'] = "background: #ed6e00; border: 1px solid #404040;"
            tdElement.append(TElement('a', text=tdElement.text, attrib={'href':str(tdElement.attrib['row'])+"x"+str(tdElement.attrib['column'])+'.xhtml', 'style':'font-weight:bold; color:#fff;'}))
            tdElement.text = None
        elif not 'style' in tdElement.attrib:
            tdElement.attrib['style'] = "background: white; color: #404040; border: 1px solid #404040"
        #dataRow.extend(tdElement)
    # print "out of loop, tabulated fp: " + str(fp)
    falseNegLinkage = TElement('td', attrib={'style':'background:#0962ac; color:#fff'})
    falseNegLinkage.append(TElement('a', text=str(fnDic[column]), attrib={'href':str(column[0])+'.xhtml', 'style':'font-weight:bold; color:#fff;'}))
    comparisonData.append(falseNegLinkage)
    comparisonData.append(TElement('td', text=str(sum(finalData[column][row] for row in values)), attrib={'style':'background:#0962ac; color: #fff'}))
    if tp != 0:
        # fscore
        #print "fscore numerator: ", (2*(float(int(tp))/float(float(int(tp)) + float(int(fp))))*(float(int(tp))/float(float(int(tp)) + float(int(fn)))))
        #print "fscore denominator: ", ((float(int(tp))/float(float(int(tp)) + float(int(fp))))+(float(int(tp))/float(float(int(tp)) + float(int(fn)))))
        fscore = TElement('td', text=str((2*(float(int(tp))/float(float(int(tp)) + float(int(fp))))*(float(int(tp))/float(float(int(tp)) + float(int(fn)))))/((float(int(tp))/float(float(int(tp)) + float(int(fp))))+(float(int(tp))/float(float(int(tp)) + float(int(fn)))))), attrib={'style':'background:#0962ac; color: #fff'})
        #print "fscore value: ", fscore.text
        comparisonData.append(fscore)
        # microrecall
        comparisonData.append(TElement('td', text=str(float(int(tp))/float(float(int(tp)) + float(int(fn)))), attrib={'style':'background:#0962ac; color: #fff'})) # tp/tp+fn
        # microprecision
        #print "dividing " + str(float(int(tp))) + " by " + str(float(int(tp)) + float(int(fp))) + " where there are %s fp's" % fp
        comparisonData.append(TElement('td', text=str(float(int(tp))/float(float(int(tp)) + float(int(fp)))), attrib={'style':'background:#0962ac; color: #fff'})) #tp/tp+fp
    elif tp == 0:
        comparisonData.append(TElement('td', text="N/A"))
        comparisonData.append(TElement('td', text="N/A"))
        comparisonData.append(TElement('td', text="N/A"))
    dataRow.extend(rowHeader)
    dataRow.extend(blankData)
    dataRow.extend(comparisonData)


listMatrix = []
spontaneousFalsePos = []
for column in values:
    # Generating nested list of values to make column tabulations easier:
    listMatrix.append([finalData[column][row] for row in values])
        

#Generating tds for tabulations of columns        
##engSumsTr = TElement('tr', parent=table)
##engSumsTh = TElement('th', text="Gs Sum", parent=engSumsTr, attrib={'style':'background:#0962ac;'})
##engSumsBlankTd = TElement('td', parent=engSumsTr)
##for i in range(len(listMatrix)):
##    td = 0
##    for j in range(len(listMatrix[i])):
##        td += listMatrix[j][i]
##    TElement('td', text=str(td), parent=engSumsTr, attrib={'style':'background:#0962ac; color: #fff'})

emptySpacing = TElement('p', parent=body)

stats = TElement('table', parent=body)
stats.attrib['style'] = "border:0px"

#Stats at a glance
baseStats = TElement('tr', parent=stats)

truePos = TElement('th', text='True Positives: ' + str(truePosCount), parent=baseStats)
falseNegs = TElement('th', text='False Negatives: ' + str(falseNegCount), parent=baseStats)
falsePos = TElement('th', text="False Positives: " + str(falsePosCount), parent=baseStats)
precision = TElement('th', text='Precision (TPs/TPs+FPs): ' + str(float(truePosCount)/float(truePosCount+falsePosCount)), parent=baseStats)
recall = TElement('th', text='Recall (TPs/TPs+FNs): ' + str(float(truePosCount)/float(truePosCount+falseNegCount)), parent=baseStats)

hrBreak = TElement('hr', parent=body)

# Want to put the spontaneous false positives into a menu below the ML stats
spontaneousFalsePos = TElement('table', parent=body)
spontaneousFalsePos.attrib['style'] = "border:0px"


tr = TElement('tr', parent=spontaneousFalsePos)
for column in values:
    th = TElement('th')
    th.append(TElement('a', text=column[0], attrib={'href':str(re.sub('[(),u\']', '', str(column)))+'_spont.xhtml', 'style':'font-weight:bold; color:#fff;'}))
    tr.append(th)
        

authorship = TElement('p', text="Email courtney.zelinsky@mmodal.com for questions / comments / suggestions for this script", parent=body)

##tooltips = TElement('script', text="""
##
##
##$(document).ready(function(){
##    var text = "".concat($(this).attr('row'), " x ", $(this).attr('column'));
##    $('td').attr('title', text);
##    $('td').hover(function(){
##        var title = $(this).attr('title');
##        $(this)
##        .data('tipText', title)
##        .removeAttr('title');
##        p = document.createElement('p');
##        $('p').addClass('tooltip')
##        .text(text)
##        .appendTo('body')
##        .fadeIn('fast');
##    }, function() {
##        $(this).attr('title', $(this).data('tipText'));
##    }).mousemove(function(e) {
##        var mousex = e.pageX + 20;
##        var mousey = e.pageY + 10;
##        $('.tooltip')
##        .css({ top: mousey, left: mousex })
##    });
##});
##""", parent=body)
#tooltips.attrib['type'] = "text/javascript"

#write matrix table to file
with open(os.path.join(path, "confusionMatrix-Deid.html"), 'w') as outputFile:
    for i in range(len(root)):
        outputFile.write(ET.tostring(root[i]))
outputFile.close()

print '\nConfusion Matrix generated -- written to ' + path
print 'Took', datetime.datetime.now()-startTime
print '\n\nStarting details file processing...'

values = sorted([key for key in finalData.keys()])

"""Creates readable xhtml output contexts"""

parser = etree.XMLParser(encoding="utf-8", recover=True)

root = TElement('root')
html = TElement('html', parent=root)
html.attrib['xmlns'] = "http://www.w3.org/1999/xhtml"

#Header
head = TElement('head', parent=html)
title = TElement('title', text="Deid Stats Results", parent=head)
css = TElement('link', parent=head)

css.attrib['href'] = "css.css"
css.attrib['type'] = "text/css"
css.attrib['rel'] = "stylesheet"

jquery = TElement('script', text="//", parent=head)
jquery.attrib['src'] = "http://code.jquery.com/jquery-1.10.2.js"

head.extend(css)
head.extend(title)
head.extend(jquery)

#Body
body = TElement('body', parent=html)
h1 = TElement('h1', text="Error contexts:", parent=body)
colorKey = TElement('p', text="Key:", parent=body)
fpKey = TElement('p', text="False Positive", parent=colorKey, attrib={'style':'background:red; width:120px;'})
fnKey = TElement('p', text="False Negative", parent=colorKey, attrib={'style':'background:gold; width:120px;'})

output = []
contexts = {}

for doc in diffsDic:
    parsedGsDoc = minidom.parse(path + '\\' + doc)
    parsedEngDoc = minidom.parse(findPair(path + '\\' + doc))
    paragraphs = []
    outputParagraph = []
    wordDict = {}
    contents = parsedEngDoc.getElementsByTagName('content')
    gsContents = parsedGsDoc.getElementsByTagName('content')
    #looks like a bunch of <DOM Element: content at 0x3396d50> etc instances for each content node in the doc
    entryTuples = [FPtuples for FPtuples in diffsDic[doc]['FP']]
    entryTuples.extend([FNtuples for FNtuples in diffsDic[doc]['FN']])
    for entry in entryTuples:
        if type(entry) != tuple:
            entryTuples.insert(entryTuples.index(entry),(entry,))
            entryTuples.remove(entry)
    #all error entry tuples, looks like [('entry_60', 'entry_61'), ('entry_201', 'entry_202'), ('entry_185', 'entry_186'), ('entry_235', 'entry_236')...]
            
    for content in contents:
        for char in ['&', ';', '<', '>']:
            if content.firstChild is not None:
                if char in content.firstChild.nodeValue:
                    wordDict[content.getAttribute('ID')] = re.sub(char, "", content.firstChild.nodeValue)
                else:
                    wordDict[content.getAttribute('ID')] = content.firstChild.nodeValue

    for i in range(len(wordDict)):
        if 'entry_' + str(i) in wordDict:
            outputParagraph.append(wordDict['entry_' + str(i)])

    #Compare the errors (entryTuples) to the indexes in the outputParagraph to see which indexes need to be overwritten
    for entry in entryTuples:
        i = 0
        for i in range(len(wordDict)):
            #Single token entry handling:
            if ('entry_' + str(i),) == entry and len(entry) == 1:
                #Something in the error list occurs at index i -- need to overwrite for this i and for this entry num

                if entry in diffsDic[doc]['FP']:
                    
                    #Last Name "He"-type spontaneous FPs
                    if entry not in gsDic[doc].keys():

                        #Multi-code
                        if len(engDic[doc][entry]) > 1:
                            for codeValue in engDic[doc][entry]:
                                if str((codeValue,))+"ONLY" not in contexts:
                                    contexts[str((codeValue,))+"ONLY"] = {}
                                outputParagraph[i] = '<error id="' + str(entry) + '" title="' + "Engine (spont): " + str(codeValue) + '"><font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(i)] + '</strong></font></error>'
                                temp = []
                                for k in range(i-10, i+10):
                                    if k >= 0 and not k > len(wordDict)-1:
                                        if k == i:
                                            #if single entry token is in compOverlaps[doc]
                                            #if entry in compOverlaps[doc].keys(): #and compOverlaps[doc]["(" + entry + ",)"] == contexts[str(engDic[doc][entry])]
                                            #temp.append('<span title="' + re.sub('[(),u\']', '', str(compOverlaps[doc][entry])) + '"><font style="background-color:purple;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                            temp.append('<font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                        elif 'entry_'+str(k) in wordDict:
                                            temp.append(wordDict['entry_' + str(k)])
                                if doc not in contexts[str((codeValue,))+"ONLY"]:
                                    contexts[str((codeValue,))+"ONLY"][doc] = []
                                contexts[str((codeValue,))+"ONLY"][doc].append(''.join(temp))
                                break

                        #Single code
                        elif len(engDic[doc][entry]) == 1:
                            if str(engDic[doc][entry])+"ONLY" not in contexts:
                                contexts[str(engDic[doc][entry])+"ONLY"] = {}
                            outputParagraph[i] = '<error id="' + str(entry) + '" title="' + "Engine (spont): " + str(engDic[doc][entry]) + '"><font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(i)] + '</strong></font></error>'
                            temp = []
                            for k in range(i-10, i+10):
                                if k >= 0 and not k > len(wordDict)-1:
                                    if k == i:
                                        #if single entry token is in compOverlaps[doc]
                                        #if entry in compOverlaps[doc].keys(): #and compOverlaps[doc]["(" + entry + ",)"] == contexts[str(engDic[doc][entry])]
                                        #temp.append('<span title="' + re.sub('[(),u\']', '', str(compOverlaps[doc][entry])) + '"><font style="background-color:purple;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                        temp.append('<font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                    elif 'entry_'+str(k) in wordDict:
                                        temp.append(wordDict['entry_' + str(k)])
                            if doc not in contexts[str(engDic[doc][entry])+"ONLY"]:
                                contexts[str(engDic[doc][entry])+"ONLY"][doc] = []
                            contexts[str(engDic[doc][entry])+"ONLY"][doc].append(''.join(temp))

                        
                    elif entry in gsDic[doc].keys():
                        
                        #FP mismatch - multicode
                        if len(engDic[doc][entry]) > 1:
                            for codeValue in engDic[doc][entry]:
                                if str(gsDic[doc][entry])+str((codeValue,)) not in contexts:
                                    contexts[str(gsDic[doc][entry])+str((codeValue,))] = {}
                                if str(gsDic[doc][entry]) != str((codeValue,)):
                                    outputParagraph[i] = '<error id="' + str(entry) + '" title="' + "Engine Mismatch: " + str(codeValue) + '" gs="' + str(gsDic[doc][entry]) + '"><font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(i)] + '</strong></font></error>'
                                    temp = []
                                    for k in range(i-10, i+10):
                                        if k >= 0 and not k > len(wordDict)-1:
                                            if k == i:
                                                #if entry in compOverlaps[doc].keys(): #and compOverlaps[doc]["(" + entry + ",)"] == contexts[str(engDic[doc][entry])]
                                                    #temp.append('<span title="' + re.sub('[(),u\']', '', str(compOverlaps[doc][entry])) + '"><font style="background-color:purple;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font></span>')
                                                temp.append('<font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                            elif 'entry_' + str(k) in wordDict:
                                            # Getting a strange issue in the xml wherein some content IDs are just being skipped completely and leaving a gap, so...
                                                temp.append(wordDict['entry_' + str(k)])
                                    if doc not in contexts[str(gsDic[doc][entry])+str((codeValue,))]:
                                        contexts[str(gsDic[doc][entry])+str((codeValue,))][doc] = []
                                    contexts[str(gsDic[doc][entry])+str((codeValue,))][doc].append(''.join(temp))

                        #FP mismatch - single code
                        elif len(engDic[doc][entry]) == 1:
                            if str(gsDic[doc][entry])+str(engDic[doc][entry]) not in contexts:
                                contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])] = {}
                            if str(gsDic[doc][entry]) != str(engDic[doc][entry]):
                                outputParagraph[i] = '<error id="' + str(entry) + '" title="' + "Engine Mismatch: " + str(engDic[doc][entry]) + '" gs="' + str(gsDic[doc][entry]) + '"><font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(i)] + '</strong></font></error>'
                                temp = []
                                for k in range(i-10, i+10):
                                    if k >= 0 and not k > len(wordDict)-1:
                                        if k == i:
                                            #if entry in compOverlaps[doc].keys(): #and compOverlaps[doc]["(" + entry + ",)"] == contexts[str(engDic[doc][entry])]
                                                #temp.append('<span title="' + re.sub('[(),u\']', '', str(compOverlaps[doc][entry])) + '"><font style="background-color:purple;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font></span>')
                                            temp.append('<font style="background-color:red;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                        elif 'entry_' + str(k) in wordDict:
                                        # Getting a strange issue in the xml wherein some content IDs are just being skipped completely and leaving a gap, so...
                                            temp.append(wordDict['entry_' + str(k)])
                                if doc not in contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])]:
                                    contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])][doc] = []
                                contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])][doc].append(''.join(temp))

           
                elif entry in diffsDic[doc]['FN']:
                    overlaps = []
                    for val in incompOverlaps[doc].keys():
                        for substring in val:
                            overlaps.append(substring)
                    overlapKeys = incompOverlaps[doc].keys()
                    overlapValues = incompOverlaps[doc].values()
                    if str(gsDic[doc][entry]) not in contexts:
                        contexts[str(gsDic[doc][entry])] = {}
                    outputParagraph[i] = '<error id="' + str(entry) + '" gs="' + str(gsDic[doc][entry]) + '"><font style="background-color:gold"><strong>' + wordDict['entry_' + str(i)] + '</strong></font></error>'
                    temp = []
                    for k in range(i-10, i+10):
                        if k >= 0 and not k > len(wordDict)-1: 
                            if k == i:
                                if 'entry_'+str(i) in overlaps:
                                    for key in overlapKeys:
                                        #Green -> token in engine AND gold standard
                                        ## Wait are these keys tuples? Check. VVV
                                        if 'entry_'+str(i) in key and 'entry_'+str(i) in overlaps:
                                            temp.append('<font style="background-color:green;color:white;"><strong>' + wordDict['entry_' + str(i)] + '</strong></font>')
                                            continue
                                #Non-overlaps Handling -- everything will just be gold
                                elif 'entry_'+str(i) not in overlaps:
                                    temp.append('<font style="background-color:gold"><strong>' + wordDict['entry_' + str(i)] + '</strong></font>')
                                    continue
                            #Blue -> token in engine
                            #Need to go through .values() -- if entry is in .values() but not in the .keys(), then bluueee
                            elif 'entry_'+str(k) in overlaps:
                                for key in overlapKeys:
                                    if 'entry_'+str(k) not in key:
                                        temp.append('<font style="background-color:blue;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                        #then will need to add one to k? so as to balance
                                        break
                            elif 'entry_'+str(k) in wordDict:
                                temp.append(wordDict['entry_' + str(k)])
                    if doc not in contexts[str(gsDic[doc][entry])]:
                        contexts[str(gsDic[doc][entry])][doc] = []
                    contexts[str(gsDic[doc][entry])][doc].append(''.join(temp))
                    
                    
            elif ('entry_' + str(i),) != entry and len(entry) > 1 and 'entry_' + str(i) == entry[0]:
                # MULTI-ENTRY HANDLING e.g. ('entry_' + str(i),) is not equal to the entry, meaning that the entry + str(i) is occuring in a multi entry
                
                if entry in diffsDic[doc]['FP'].keys():
                    #if entry is a spontaneous multi-entry fp
                    if entry not in gsDic[doc].keys():
                        
                        if len(engDic[doc][entry]) > 1:
                            #multi-code spontaneous multi-entry
                            for codeValue in engDic[doc][entry]:
                                if str((codeValue,))+"ONLY" not in contexts:
                                    contexts[str((codeValue,))+"ONLY"] = {}
                                for j in range(0, len(entry)):
                                    outputParagraph[i+j] = '<error id="' + str(entry) + '" title="' + str(codeValue) + '"><font style="background-color:red;color:white;"><strong>' + wordDict[entry[j]] + '</strong></font></error>'
                                temp = []
                                k = i-10
                                while (k < (i + 10)):
                                    if k >= 0 and not k > len(wordDict)-1:
                                        if k == i:
                                            temp.append('<font style="background-color:red;color:white;"><strong>' + "".join([wordDict['entry_' + str(i+m)] for m in range(0, len(entry))]) + '</strong></font>')
                                            k += len(entry)
                                            continue
                                        elif 'entry_'+str(k) in wordDict:
                                            temp.append(wordDict['entry_' + str(k)])
                                    k += 1
                                if doc not in contexts[str((codeValue,))+"ONLY"]:
                                    contexts[str((codeValue,))+"ONLY"][doc] = []
                                contexts[str((codeValue,))+"ONLY"][doc].append(''.join(temp))
                                break
                                
                        #single-code spontaneous multi-entry
                        elif len(engDic[doc][entry]) == 1:
                            if str(engDic[doc][entry])+"ONLY" not in contexts:
                                contexts[str(engDic[doc][entry])+"ONLY"] = {}
                            for j in range(0, len(entry)):
                                outputParagraph[i+j] = '<error id="' + str(entry) + '" title="' + str(engDic[doc][entry]) + '"><font style="background-color:red;color:white;"><strong>' + wordDict[entry[j]] + '</strong></font></error>'
                            temp = []
                            k = i-10
                            while (k < (i + 10)):
                                if k >= 0 and not k > len(wordDict)-1:
                                    if k == i:
                                        temp.append('<font style="background-color:red;color:white;"><strong>' + "".join([wordDict['entry_' + str(i+m)] for m in range(0, len(entry))]) + '</strong></font>')
                                        k += len(entry)
                                        continue
                                    elif 'entry_'+str(k) in wordDict:
                                        temp.append(wordDict['entry_' + str(k)])
                                k += 1
                            if doc not in contexts[str(engDic[doc][entry])+"ONLY"]:
                                contexts[str(engDic[doc][entry])+"ONLY"][doc] = []
                            contexts[str(engDic[doc][entry])+"ONLY"][doc].append(''.join(temp))

                    # If entry is a mismatch multi-entry fp
                    elif entry in gsDic[doc].keys():
                        if len(engDic[doc][entry]) > 1:
                            for codeValue in engDic[doc][entry]:
                                if str(gsDic[doc][entry])+str((codeValue,)) not in contexts:
                                    contexts[str(gsDic[doc][entry])+str((codeValue,))] = {}
                                if str(gsDic[doc][entry]) != str((codeValue,)):
                                    for j in range(0, len(entry)):
                                        outputParagraph[i+j] = '<error id="' + str(entry) + '" gs="' + str(gsDic[doc][entry]) + '" title="' + "Engine (spont): " + str(codeValue) + '"><font style="background-color:red;color:white;"><strong>' + wordDict[entry[j]] + '</strong></font></error>'
                                    temp = []
                                    k = i-10
                                    while (k < (i + 10)):
                                        if k >= 0 and not k > len(wordDict)-1:
                                            if k == i:
                                                temp.append('<font style="background-color:red;color:white;"><strong>' + "".join([wordDict['entry_' + str(i+m)] for m in range(0, len(entry))]) + '</strong></font>')
                                                k += len(entry)
                                                continue
                                            elif 'entry_'+str(k) in wordDict:
                                                temp.append(wordDict['entry_' + str(k)])
                                        k += 1
                                    if doc not in contexts[str(gsDic[doc][entry])+str((codeValue,))]:
                                        contexts[str(gsDic[doc][entry])+str((codeValue,))][doc] = []
                                    contexts[str(gsDic[doc][entry])+str((codeValue,))][doc].append(''.join(temp))

                        elif len(engDic[doc][entry]) == 1:
                            if str(gsDic[doc][entry])+str(engDic[doc][entry]) not in contexts:
                                contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])] = {}
                            if str(gsDic[doc][entry]) != str(engDic[doc][entry]):
                                for j in range(0, len(entry)):
                                    outputParagraph[i+j] = '<error id="' + str(entry) + '" gs="' + str(gsDic[doc][entry]) + '" title="' + "Engine (spont): " + str(engDic[doc][entry]) + '"><font style="background-color:red;color:white;"><strong>' + wordDict[entry[j]] + '</strong></font></error>'
                                temp = []
                                k = i-10
                                while (k < (i + 10)):
                                    if k >= 0 and not k > len(wordDict)-1:
                                        if k == i:
                                            temp.append('<font style="background-color:red;color:white;"><strong>' + "".join([wordDict['entry_' + str(i+m)] for m in range(0, len(entry))]) + '</strong></font>')
                                            k += len(entry)
                                            continue
                                        elif 'entry_'+str(k) in wordDict:
                                            temp.append(wordDict['entry_' + str(k)])
                                    k += 1
                                if doc not in contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])]:
                                    contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])][doc] = []
                                contexts[str(gsDic[doc][entry])+str(engDic[doc][entry])][doc].append(''.join(temp))

                # If entry is a multi-entry fn
                elif entry in diffsDic[doc]['FN'].keys():
                    overlaps = []
                    for val in incompOverlaps[doc].values():
                        for substring in val:
                            overlaps.append(substring)
                    overlapKeys = incompOverlaps[doc].keys()
                    overlapValues = incompOverlaps[doc].values()
                    #using other variables to make the below overlaps procedure less painful
                    if str(diffsDic[doc]['FN'][entry]) not in contexts:
                        contexts[str(diffsDic[doc]['FN'][entry])] = {}
                    temp = []
                    for j in range(0, len(entry)):
                    #for each entry number in the multi-entry tuple
                        outputParagraph[i+j] = '<error id="' + str(entry) + '" gs="' + str(gsDic[doc][entry]) + '"><font style="background-color:gold"><strong>' + wordDict[entry[j]] + '</strong></font></error>'
                    k = i-10
                    while (k < (i + 10)):
                        if k >= 0 and not k > len(wordDict)-1:
                            if k == i:
                                for m in range(0, len(entry)):
                                    #FN Overlap Handling:
                                    if 'entry_'+str(i+m) in overlaps:
                                        for key in overlapKeys:
                                            #Green -> token in engine AND gold standard
                                            if 'entry_'+str(i+m) in key and 'entry_'+str(i+m) in overlaps:
                                                #if key != 'entry_'+str(i+m):
                                                temp.append('<font style="background-color:green;color:white;"><strong>' + wordDict['entry_' + str(i+m)] + '</strong></font>')
                                                break
                                    #Non-overlaps Handling -- everything will just be gold
                                    elif 'entry_'+str(i+m) not in overlapValues:
                                        temp.append('<font style="background-color:gold"><strong>' + wordDict['entry_' + str(i+m)] + '</strong></font>')
                                        continue
                                k += len(entry)
                                continue
                            #Blue -> token in engine
                            elif 'entry_'+str(k) in overlaps:
                                for key in overlapKeys:
                                    if 'entry_'+str(k) not in key:
                                        temp.append('<font style="background-color:blue;color:white;"><strong>' + wordDict['entry_' + str(k)] + '</strong></font>')
                                        #then will need to add one to k? so as to balance
                                        break
                            elif 'entry_'+str(k) in wordDict:
                                temp.append(wordDict['entry_' + str(k)])
                        k += 1
                    if doc not in contexts[str(gsDic[doc][entry])]:
                        contexts[str(gsDic[doc][entry])][doc] = []
                    contexts[str(gsDic[doc][entry])][doc].append(''.join(temp))
                    #break
                        #print "MULTI FN ENTRY GENERATED IN CONFUSION ", str(gsDic[doc][entry])
                i += len(entry)

    output.append('<context doc="' + doc + '">' + "".join(outputParagraph) + '</context>')

output = "<contexts>" + "".join(output) + "</contexts>"

allContexts = path + "allContexts.xhtml"
with open(os.path.join(path, allContexts), 'w') as allContextsXML:
    allContextsXML.write(output)
allContextsXML.close()

#reparsing the output so as to proceed to add it to a final xhtml format:
finalOutput = ET.parse(allContexts, parser=parser)

allContextsPerDoc = finalOutput.findall('context')
    
allContextsTable = TElement('table', parent=body)
allContextsTable.attrib['id'] = "KWIC"

for context in allContextsPerDoc:
    allContextsTable.append(TElement('h3', text=context.get('doc')))
    allContextsTable.append(context)
    allContextsTable.append(TElement('p', parent=allContextsTable))

# for the file it's hashed to, if some entry numbers appeared in false positives or false negatives, get all text descendents from paragraph nodes 
with open(os.path.join(path, "KWIC_out.xhtml"), 'w') as outputFile:
    for i in range(len(root)):
        outputFile.write(ET.tostring(root[i]))
outputFile.close()

print "Now generating individual details files..."

#want to do a findall for each combination of error and FN combinations greater than 0

kwicParsed = minidom.parse(path + '\\' + "KWIC_out.xhtml")

parser = etree.XMLParser(recover=True)

#FN File Handling
for column in values:
    if fnDic[column] > 0:
    #for row in values:
        #if finalData[column][row] > 0 and column != row:
        #if the stat is non-zero and not a true positive
        #print "column: ", column
        Doc = minidom.Document()
        rootTemp = Doc.createElement('html')
        rootTemp.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
        
        #Header
        head = Doc.createElement('head')
        rootTemp.appendChild(head)
        
        title = Doc.createElement('title')
        titleText = Doc.createTextNode(re.sub('[(),u\']', '', str(column)) + " results")
        title.appendChild(titleText)
        head.appendChild(title)
        
        css = Doc.createElement('link')
        css.setAttribute('href', 'css.css')
        css.setAttribute('type', 'text/css')
        css.setAttribute('rel', 'stylesheet')
        head.appendChild(css)

        jquery = Doc.createElement('script')
        jquery.setAttribute('src', 'http://code.jquery.com/jquery-1.10.2.js')
        jqueryText = Doc.createTextNode('//')
        jquery.appendChild(jqueryText)
        head.appendChild(jquery)
        
        rootTemp.appendChild(head)
        
        #Body
        body = Doc.createElement('body')
        h1 = Doc.createElement('h1')
        h1Text = Doc.createTextNode(re.sub('[(),u\']', '', str(column)))
        h1.appendChild(h1Text)
        
        colorKey = Doc.createElement('p')

        fnKeys = Doc.createElement('p')

        fn = Doc.createElement('span')
        fnTitle = Doc.createTextNode('False Negative: ')
        fn.appendChild(fnTitle)
        fnKeys.setAttribute('style', 'font-weight:bold;')
        fnKeys.appendChild(fn)

        fnKey = Doc.createElement('span')
        fnKeyText = Doc.createTextNode('Gold Standard ')
        fnKey.appendChild(fnKeyText)
        fnKey.setAttribute('style', 'background:gold; width:120px;')
        fnKeys.appendChild(fnKey)

        overlapKey = Doc.createElement('span')
        overlapKeyText = Doc.createTextNode(' Overlap ')
        overlapKey.appendChild(overlapKeyText)
        overlapKey.setAttribute('style', 'background:green; color:white; width:100px;')
        fnKeys.appendChild(overlapKey)

        engineKey = Doc.createElement('span')
        engineKeyText = Doc.createTextNode(' Engine Output')
        engineKey.appendChild(engineKeyText)
        engineKey.setAttribute('style', 'background:blue; color:white; width:120px;')
        fnKeys.appendChild(engineKey)

        colorKey.appendChild(fnKeys)

        body.appendChild(h1)
        body.appendChild(colorKey)

        contextsTable = Doc.createElement('table')

        if str(column) in contexts:
            for docName, snippets in contexts[str(column)].items():
                contextNode = Doc.createElement('ul')
                docNode = Doc.createElement('h3')
                docText = Doc.createTextNode(docName)
                docNode.appendChild(docText)
                contextNode.appendChild(docNode)
                for snippet in snippets:
                    for char in ['&', '; ', ' < ', ' > ', '<INC']:
                        while char in snippet:
                            snippet = "<p>" + re.sub(char, "", snippet)+ "</p>"
                        snippetClean = "<p>" + snippet + "</p>"
                    parsedSnippet = minidom.parseString(snippetClean.encode('utf-8'))
                    finalSnippet = parsedSnippet.firstChild
                    contextNode.appendChild(finalSnippet)
                contextsTable.appendChild(contextNode)

            body.appendChild(contextsTable)
            rootTemp.appendChild(body)
            Doc.appendChild(rootTemp)
            f = re.sub('[(),u\']', '', str(column)) + ".xhtml"
            #f = re.sub('[(),u\']', '', str(column)) + "x" + re.sub('[(),u\']', '', str(row)) + ".xhtml"
            with open(os.path.join(path, f), 'w') as output:
                output.write(Doc.toxml())
            output.close()

#FP Mismatch File Handling
for column in values:
    for row in values:
        if finalData[column][row] > 0 and column != row:
        #if the stat is non-zero and not a true positive               
            #print "column: ", column, " row: ", row
            Doc = minidom.Document()
            rootTemp = Doc.createElement('html')
            rootTemp.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
            
            #Header
            head = Doc.createElement('head')
            rootTemp.appendChild(head)
            
            title = Doc.createElement('title')
            titleText = Doc.createTextNode(re.sub('[(),u\']', '', str(column)) + " results")
            title.appendChild(titleText)
            head.appendChild(title)
            
            css = Doc.createElement('link')
            css.setAttribute('href', 'css.css')
            css.setAttribute('type', 'text/css')
            css.setAttribute('rel', 'stylesheet')
            head.appendChild(css)

            jquery = Doc.createElement('script')
            jquery.setAttribute('src', 'http://code.jquery.com/jquery-1.10.2.js')
            jqueryText = Doc.createTextNode('//')
            jquery.appendChild(jqueryText)
            head.appendChild(jquery)
            
            rootTemp.appendChild(head)
            
            #Body
            body = Doc.createElement('body')
            h1 = Doc.createElement('h1')
            h1Text = Doc.createTextNode(re.sub('[(),u\']', '', str(column)) + " mistaken for " + re.sub('[(),u\']', '', str(row)))
            h1.appendChild(h1Text)
            
            colorKey = Doc.createElement('p')

            fp = Doc.createElement('span')
            fpTitle = Doc.createTextNode('False Positive: ')
            fp.appendChild(fpTitle)
            fp.setAttribute('style', 'font-weight:bold;')

            fpKey = Doc.createElement('span')
            fpKeyText = Doc.createTextNode('Engine Output ')
            fpKey.appendChild(fpKeyText)
            fpKey.setAttribute('style', 'background:red; color:white; width:120px;')

            colorKey.appendChild(fp)
            colorKey.appendChild(fpKey)

            body.appendChild(h1)
            body.appendChild(colorKey)

            contextsTable = Doc.createElement('table')

            if str(column)+str(row) in contexts:    
                for docName, snippets in contexts[str(column)+str(row)].items():
                    contextNode = Doc.createElement('ul')
                    docNode = Doc.createElement('h3')
                    docText = Doc.createTextNode(docName)
                    docNode.appendChild(docText)
                    contextNode.appendChild(docNode)
                    for snippet in snippets:
                        for char in ['&', '; ', ' < ', ' > ', '<INC']:
                            while char in snippet:
                                snippet = "<p>" + re.sub(char, "", snippet)+ "</p>"
                            snippetClean = "<p>" + snippet + "</p>"
                        parsedSnippet = minidom.parseString(snippetClean.encode('utf-8'))
                        finalSnippet = parsedSnippet.firstChild
                        contextNode.appendChild(finalSnippet)
                    contextsTable.appendChild(contextNode)
                        
            body.appendChild(contextsTable)
            rootTemp.appendChild(body)
            Doc.appendChild(rootTemp)
            f = re.sub('[(),u\']', '', str(column)) + "x" + re.sub('[(),u\']', '', str(row)) + ".xhtml"
            #f = re.sub('[(),u\']', '', str(column)) + "x" + re.sub('[(),u\']', '', str(row)) + ".xhtml"
            with open(os.path.join(path, f), 'w') as output:
                output.write(Doc.toxml())
            output.close()

#Spontaneous FP Handling
for column in values:
    for row in values:
        if finalData[column][row] > 0 and column != row:
        #if the stat is non-zero and not a true positive               
            #print "column: ", column, " row: ", row
            Doc = minidom.Document()
            rootTemp = Doc.createElement('html')
            rootTemp.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
            
            #Header
            head = Doc.createElement('head')
            rootTemp.appendChild(head)
            
            title = Doc.createElement('title')
            titleText = Doc.createTextNode(re.sub('[(),u\']', '', str(column)) + " results")
            title.appendChild(titleText)
            head.appendChild(title)
            
            css = Doc.createElement('link')
            css.setAttribute('href', 'css.css')
            css.setAttribute('type', 'text/css')
            css.setAttribute('rel', 'stylesheet')
            head.appendChild(css)

            jquery = Doc.createElement('script')
            jquery.setAttribute('src', 'http://code.jquery.com/jquery-1.10.2.js')
            jqueryText = Doc.createTextNode('//')
            jquery.appendChild(jqueryText)
            head.appendChild(jquery)
            
            rootTemp.appendChild(head)
            
            #Body
            body = Doc.createElement('body')
            h1 = Doc.createElement('h1')
            h1Text = Doc.createTextNode(re.sub('[(),u\']', '', str(column)) + " (Spontaneous)")
            h1.appendChild(h1Text)
            
            colorKey = Doc.createElement('p')

            fp = Doc.createElement('span')
            fpTitle = Doc.createTextNode('False Positive: ')
            fp.appendChild(fpTitle)
            fp.setAttribute('style', 'font-weight:bold;')

            fpKey = Doc.createElement('span')
            fpKeyText = Doc.createTextNode('Engine Output ')
            fpKey.appendChild(fpKeyText)
            fpKey.setAttribute('style', 'background:red; color:white; width:120px;')

            colorKey.appendChild(fp)
            colorKey.appendChild(fpKey)

            body.appendChild(h1)
            body.appendChild(colorKey)

            contextsTable = Doc.createElement('table')
            
            if str(column)+"ONLY" in contexts:
                for docName, snippets in contexts[str(column)+"ONLY"].items():
                    contextNode = Doc.createElement('ul')
                    docNode = Doc.createElement('h3')
                    docText = Doc.createTextNode(docName)
                    docNode.appendChild(docText)
                    contextNode.appendChild(docNode)
                    for snippet in snippets:
                        for char in ['&', '; ', ' < ', ' > ', '<INC']:
                            while char in snippet:
                                snippet = "<p>" + re.sub(char, "", snippet) + "</p>"
                            snippetClean = "<p>" + snippet + "</p>"
                        parsedSnippet = minidom.parseString(snippetClean.encode('utf-8'))
                        finalSnippet = parsedSnippet.firstChild
                        contextNode.appendChild(finalSnippet)
                    contextsTable.appendChild(contextNode)

            body.appendChild(contextsTable)
            rootTemp.appendChild(body)
            Doc.appendChild(rootTemp)
            f = re.sub('[(),u\']', '', str(column)) + "_spont.xhtml"
            with open(os.path.join(path, f), 'w') as output:
                output.write(Doc.toxml())
            output.close()
            
print '\nDetails file(s) generated -- written to ' + path
print datetime.datetime.now()-startTime, 'to run', len(docs)/2, 'file(s).'
