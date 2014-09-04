# -*- coding: utf-8 -*-
## author : Courtney Zelinsky
## created : 5/13/14
##
## Call on cmd line with arg[1] = path containing all files for testing, gs files in the format ~.xml and their engine counterparts ~.out.xml
##
## Henry's wishlist:
## "There were 2 minor warts I know of in the code.  
## 1)	It's insufficiently clear if columns are the gold or test set.
## 2)	There is no link from confusion matrix to details files."
##
import datetime, os, xml.dom.minidom, datetime, operator, pickle, sys, libxml2, collections, repr
from xml.dom.minidom import parse
import xml.dom.minidom as minidom
import xml.etree.ElementTree
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element, tostring, SubElement, XML
from xml.etree.ElementTree import XMLParser
from lxml import etree


startTime = datetime.datetime.now()
#path = sys.argv[1]
path = "C:/Users/courtney.zelinsky/Desktop/deid"

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

def findPair(fname): 
    return fname[:-3] + 'out.xml'

#truePositivesMaster = {"B~ClinicalDocument_2531456463.xml":{('entry_60', 'entry_61'): (u'ABSOLUTE_DATE',), ('entry_201', 'entry_202'): (u'ABSOLUTE_DATE',), ('entry_185', 'entry_186'): (u'ABSOLUTE_DATE',), ('entry_235', 'entry_236'): (u'ABSOLUTE_DATE',), ('entry_20', 'entry_21'): (u'ABSOLUTE_DATE',), ('entry_282',): (u'LAST_NAME',), ('entry_144', 'entry_145'): (u'ABSOLUTE_DATE',), ('entry_18', 'entry_19'): (u'ABSOLUTE_DATE',), ('entry_140', 'entry_141'): (u'ABSOLUTE_DATE',), ('entry_244', 'entry_245'): (u'ABSOLUTE_DATE',), ('entry_566',): (u'LOCATION',), ('entry_216', 'entry_217'): (u'ABSOLUTE_DATE',), ('entry_13', 'entry_14', 'entry_15'): (u'ABSOLUTE_DATE',), ('entry_85', 'entry_86'): (u'ABSOLUTE_DATE',), ('entry_131', 'entry_132'): (u'ABSOLUTE_DATE',), ('entry_256', 'entry_257'): (u'ABSOLUTE_DATE',), ('entry_388',): (u'LAST_NAME',), ('entry_8',): (u'LAST_NAME',), ('entry_271', 'entry_272'): (u'ABSOLUTE_DATE',), ('entry_7',): (u'FEMALE_NAME',), ('entry_228', 'entry_229'): (u'ABSOLUTE_DATE',), ('entry_70', 'entry_71'): (u'ABSOLUTE_DATE',), ('entry_285',): (u'AGE',), ('entry_103', 'entry_104'): (u'ABSOLUTE_DATE',)}}
#just using truePositives for testing here, but this will be the format when an error dictionary is established
#Need FP and FN from each doc, preferably in format {doc:{FP:{entry:code, entry:code, ...}, FN:{entry:code, entry:code}}}


def KWIC(truePositivesMaster):
    """Creates readable xhtml output contexts """
    
    parser = XMLParser(encoding="utf-8")

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
    values = sorted([key for key in confusionMatrix.keys()])
    body = TElement('body', parent=html)
    h1 = TElement('h1', text="Error contexts:", parent=body)

    output = []
    
    for doc in errors:
        parsedDoc = minidom.parse(findPair(path + '\\' + doc))
        paragraphs = []
        outputParagraph = []
        wordDict = {}
        #paragraphs = parsedDoc.getElementsByTagName('paragraphs')
        contents = parsedDoc.getElementsByTagName('content')
        #looks like a bunch of <DOM Element: content at 0x3396d50> etc instances for each content node in the doc
        entryTuples = [FPtuples for FPtuples in errors[doc]['FP']]
        print doc + ": "
        print "entryTuples (before) : ", entryTuples
        entryTuples.extend([FNtuples for FNtuples in errors[doc]['FN']])
        print "entryTuples (after) : ", entryTuples
        for entry in entryTuples:
            if type(entry) != tuple:
                print type(entry)
                print "the entry type wasn't a tuple, and so attempting to reinsert " + entry + " at the same index as a tuple"
                entryTuples.insert(entryTuples.index(entry),(entry,))
                entryTuples.remove(entry)
        #all error entry tuples, looks like [('entry_60', 'entry_61'), ('entry_201', 'entry_202'), ('entry_185', 'entry_186'), ('entry_235', 'entry_236')...]
        for content in contents:
            if content.firstChild is not None:
                wordDict[content.getAttribute('ID')] = content.firstChild.nodeValue
            #entry number to token dictionary, looks like {u'entry_567': u'this ', u'entry_566': u'Boston ', u'entry_565': u'in ', u'entry_564': u'appointment '
        for i in range(len(wordDict)):
            # Preprocessing (getting a problem with parser not able to handle u'<INC ', u'00:04:36> ' -type of markup in the document) 
            if not '>' in wordDict['entry_' + str(i)] and not '<' in wordDict['entry_' + str(i)] and not ';' in wordDict['entry_' + str(i)]:
                if '&' in wordDict['entry_' + str(i)]:
                    outputParagraph.append(wordDict['entry_' + str(i)].replace("&", "&amp;"))
                else:
                    outputParagraph.append(wordDict['entry_' + str(i)])
        #for entries in entryTuples:
            #pass
            #for entry in entries:
            #looking at each entry number individually , applies the CSS individually -- not sure if i could easily apply the CSS for the full tuple?
            #if len(entries) > 1:
            #    for subentry in entries:
            #        print subentry
            #        entryTuples.append((subentry,))
            #    entryTuples.remove(entries)

        for entry in entryTuples:
            for i in range(len(wordDict)):
                if ('entry_' + str(i),) == entry : #or 'entry_' + str(i) == entry in:
                    if entry in errors[doc]['FP']:
                        if entry not in gsDic[doc]:
                            outputParagraph[i] = '<font style="background-color:red"><strong><error id="' + str(entry) + '" gs="ENGINE_ONLY_ENTRY" eng="' + str(errors[doc]['FP'][entry])  + '">' + wordDict['entry_' + str(i)] + '</error></strong></font>'
                        else:
                            outputParagraph[i] = '<font style="background-color:red"><strong><error id="' + str(entry) + '" gs="' + str(gsDic[doc][entry]) + '" eng="' + str(errors[doc]['FP'][entry])  + '">' + wordDict['entry_' + str(i)] + '</error></strong></font>'
                    elif entry in errors[doc]['FN']:
                        outputParagraph[i] = '<font style="background-color:gold"><strong><error id="' + str(entry) + '" gs="GS_ONLY_ENTRY" eng="' + str(errors[doc]['FN'][entry])  + '">' + wordDict['entry_' + str(i)] + '</error></strong></font>'
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

#for engine only or gs only MIMs
fnDic = {}
fpDic = {}
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
        
        print "\n\n_______________________________________\n"
        print "Now parsing document %s out of %s..." % (docCount, len(docs)/2)
        print "_______________________________________\n\n"
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
                    bindings.extend([narrativeBindings.getAttribute('ref') for narrativeBindings in child.childNodes])
                    entries = tuple(str(binding) for binding in bindings if len(binding)>0)
                    value = [child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code'] # added if filter here, because why would we need the manual validation codes? 
                    gsDic[doc][entries] = value
        for k, v in gsDic[doc].items():
            gsDic[doc][k] = tuple(v)

        #print "gsDic : ", gsDic 
                        
        # if the gold standard isn't perfect + has overlapping entries, it will be seen here but is not yet tested/fixed

        # --> Create alert that funnels gs documents having overlapping MIMs and output at end of script
        
        ## Establishing the engine data structures
        engDic[doc] = {}
        entries = parsedEngDoc.getElementsByTagName('entry')
        for entry in entries:
            bindings = []
            for child in entry.firstChild.childNodes:
                if child.localName == 'binding':
                    bindings.extend([narrativeBindings.getAttribute('ref') for narrativeBindings in child.childNodes])
                    entries = tuple(str(binding) for binding in bindings if len(binding)>0)
                    value = [child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code'] # added if filter here, because why would we need the manual validation codes? 
                    if entries in engDic[doc]:
                        engDic[doc][entries].append("".join(value))
                    else:
                        engDic[doc][entries] = value
        for k, v in engDic[doc].items():
            engDic[doc][k] = tuple(v)
         
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
        #False positives: 
        engDiffs = {entry:engDic[doc][entry] for entry in engDic[doc] if entry not in gsDic[doc]}

        engDiffsOneToOne = {}
        for entry in engDiffs:
            if len(entry) > 1:
                for subentry in entry:
                    engDiffsOneToOne[(subentry,)] = engDiffs[entry]
            else:
                engDiffsOneToOne[entry] = engDiffs[entry]

        gsDiffsOneToOne = {}
        for entry in gsDiffs:
            if len(entry) > 1:
                for subentry in entry:
                    gsDiffsOneToOne[(subentry,)] = gsDiffs[entry]
            else:
                gsDiffsOneToOne[entry] = gsDiffs[entry]

        # errors has the structure {doc:{"FN":{entry:code, ...}, "FP":{entry:code, ...} }
        # -> being used by KWIC to provide error highlighting in contexts -- created the above 1:1 dics to facilitate that process for multi-token Mims
        errors[doc] = {}
        errors[doc]["FN"] = {}
        errors[doc]["FN"] = gsDiffsOneToOne
        errors[doc]["FP"] = {}
        errors[doc]["FP"] = engDiffsOneToOne

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
                        print "code that is in engDic[doc][entry]: ", code
                        if code not in gsDic[doc][entry]:
                            print "code that is not in gsDic[doc][entry]: ", code
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
                print "initialized a false negative entry"

        ### gsDiffs = What the gold standard said was right ###
        ### engineDiffs = What the engine said was right ###

        print "\n\nDifferences in engine versus gold standard - " + doc + ":"
        print "_____________________________________________\n"
        print "In gold standard version but not in engine version (false negatives): (x%s found)" % len(gsDiffs)
        falseNegCount += len(gsDiffs)
        #print gsDiffs
        print ""
        #print "In engine version but not in gold standard version (false positives): (x%s found)" % len(engDiffs)
        falsePosCount += len(engDiffs)
        #print engDiffs
        print "\n\n"
        ### engineDiffs will contain false positives, scopeMismatchValueMatches, and ScopeMatchValueMismatch
        
        # Checking for false positives:
        #  defining false positives as just what falls in the above after mismatches are picked out ###
        gsDiffsEntries = gsDiffs.keys()
        engineDiffsEntries = engDiffs.keys()
        engDiffsEntries = engineDiffsEntries
        
        # Checking for scope match, value mismatch (Same entry number, different code value):
##        scopeMatchValueMismatch = []

##        print("~")
##        print "engine diffs entries: ", engineDiffsEntries
##        print("-----")
##        print "gs diffs entries: ", gsDiffsEntries
##        print("~")
##        for i in range(len(engDiffsEntries)):
##            for j in range(len(gsDic[doc])):
##            # Comparing against true positives
##                if engDiffsEntries[i] == gsDic[doc].keys()[i]:
##                # in other words, if the scopes (read: the tuple of entry numbers) are the same, then...
##                    print engineDiffsEntries[i] + " was confused for the correct mim code " + gsDic[doc][gsDic[doc].keys()[j]]
##                    scopeMatchValueMismatch.append(gsDic[j][0])
##        print "scope match value mismatch mims: ", scopeMatchValueMismatch
                    
        # Get each gs diff entry (ede -- engine diff entry)
##        for gde in gsDiffsEntries:
##            # Get the key (a tuple) of each gold standard dic item
##            for key in gsDic[doc].keys():
##                # Convert each to a string for easy comparison
##                strGDE = str(gde)
##                strKey = str(key)
##                if strGDE == strKey:
                    #print("same")
        # Checking for overlap

##        print("\nOverlap handling\n")
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
        #print "x%s mismatch instance(s) of proper scope but incorrect value involving entry number(s):\n" % len(scopeMatchValueMismatch)
        #print scopeMatchValueMismatch
        #print "\n"
##        scopeMatchValueMismatchEntryNums = [entryNum for entryNum in scopeMatchValueMismatch]
##        entryJustNumsList = []
##        for entry in scopeMatchValueMismatchEntryNums:
##            for subentry in entry:
##                entryJustNumsList.append(subentry.split("_")[1])
##
        # Checking for scope mismatch, value match (Overlapping entry numbers, same code value)
        #
        # Test cases: "in October" vs "October" for DATE, "on October 21 1993" and "October 21 1993" as ABSOLUTE_DATE
        # --> entry is in tuple but engine result tuple and gs tuple are different lengths
##        engDiffsEntries = {}
##        print "\n\nScope Mismatch - Value Match MIMs:"
##        print "_____________________________________________\n"
##        scopeMismatchValueMatch = []
##        
##        for i in range(len(gsWorkingData)):
##            for j in range(len(engineDiffsList)):
##                for k in range(len(engineDiffsList[j][0])):
##                    if engineDiffsList[j][0][k] in gsWorkingData[i][0] and engineDiffsList[j] not in scopeMismatchValueMatch:
##                        #want to be checking if scope are same / diff using the truePos list too
##                        scopeMismatchValueMatch.append(engineDiffsList[j]);
##        print "Scoping was problematic involving %s MIMs, which were:" % len(scopeMismatchValueMatch)
##        print scopeMismatchValueMatch
        # Totals
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

print 'Totals'
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
tableHeaders = [ TElement('th', text=column[0]) for column in values]
tableHeaders.append(TElement('th', text="Eng Sum", attrib={'style':'background:#0962ac;'}))
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
    rowHeader = TElement('th', text=column[0], parent=dataRow)
    blankData = TElement('td', parent=dataRow)
    blankData.attrib['style'] = "border:0px"
    for row in values:
        fn = fnDic[row]
        comparisonData = [TElement('td', text=str(finalData[column][row]), attrib={'column':row[0]}) for row in values]
        comparisonData.append(TElement('td', text=str(sum(finalData[column][row] for row in values)), attrib={'style':'background:#0962ac; color: #fff'}))
        for tdElement in comparisonData[:-1]:
            tdElement.attrib['row'] = column[0]
            if tdElement.attrib['column'] == tdElement.attrib['row']:
                tp = int(tdElement.text)
                tdElement.attrib['style'] = "background: #00cd00; border: 1px solid #404040"
            elif tdElement.text != '0' and tdElement.attrib['column'] != tdElement.attrib['row'] :
                fp += int(tdElement.text)
                print "current fp: " + str(fp)
                tdElement.attrib['style'] = "background: #ed6e00; border: 1px solid #404040"
            else:
                tdElement.attrib['style'] = "background: white; color: #404040; border: 1px solid #404040"
            dataRow.extend(tdElement)
        print "fn ", fn, " for row ", row
        # print "out of loop, tabulated fp: " + str(fp)
        if tp != 0:
            # fscore
            print "fscore numerator: ", (2*(float(int(tp))/float(float(int(tp)) + float(int(fp))))*(float(int(tp))/float(float(int(tp)) + float(int(fn)))))
            print "fscore denominator: ", ((float(int(tp))/float(float(int(tp)) + float(int(fp))))+(float(int(tp))/float(float(int(tp)) + float(int(fn)))))
            fscore = TElement('td', text=str((2*(float(int(tp))/float(float(int(tp)) + float(int(fp))))*(float(int(tp))/float(float(int(tp)) + float(int(fn)))))/((float(int(tp))/float(float(int(tp)) + float(int(fp))))+(float(int(tp))/float(float(int(tp)) + float(int(fn)))))), attrib={'style':'background:white; color: #404040;'})
            print "fscore value: ", fscore.text
            comparisonData.append(fscore)
            # microrecall
            comparisonData.append(TElement('td', text=str(float(int(tp))/float(float(int(tp)) + float(int(fn)))), attrib={'style':'background:white; color: #404040;'})) # tp/tp+fn
            # microprecision
            print "dividing " + str(float(int(tp))) + " by " + str(float(int(tp)) + float(int(fp))) + " where there are %s fp's" % fp
            comparisonData.append(TElement('td', text=str(float(int(tp))/float(float(int(tp)) + float(int(fp)))), attrib={'style':'background:white; color: #404040;'})) #tp/tp+fp
            break
        elif tp == 0:
            comparisonData.append(TElement('td', text="N/A"))
            comparisonData.append(TElement('td', text="N/A"))
            comparisonData.append(TElement('td', text="N/A"))
    dataRow.extend(rowHeader)
    dataRow.extend(blankData)
    dataRow.extend(comparisonData)

# Generating nested list of values to make column tabulations easier:
listMatrix = []
for column in values:
        listMatrix.append([finalData[column][row] for row in values])

#Generating tds for tabulations of columns        
engSumsTr = TElement('tr', parent=table)
engSumsTh = TElement('th', text="Gs Sum", parent=engSumsTr, attrib={'style':'background:#0962ac;'})
engSumsBlankTd = TElement('td', parent=engSumsTr)
for i in range(len(listMatrix)):
    td = 0
    for j in range(len(listMatrix[i])):
        td += listMatrix[j][i]
    TElement('td', text=str(td), parent=engSumsTr, attrib={'style':'background:#0962ac; color: #fff'})


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

# KWIC examination text to go here in html

# for the file it's hashed to, if some entry numbers appeared in false positives or false negatives, get all text descendents from paragraph nodes 

#write matrix table to file
with open(os.path.join(path, "confusionMatrix-Deid.html"), 'w') as outputFile:
    for i in range(len(root)):
        outputFile.write(ET.tostring(root[i]))
outputFile.close()

print '\nConfusion Matrix generated -- written to ' + path
print 'Took', datetime.datetime.now()-startTime, 'to run', len(docs)/2, 'file(s).'

KWIC(errors)
