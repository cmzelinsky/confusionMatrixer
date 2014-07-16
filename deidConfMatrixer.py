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



import datetime, os, xml.dom.minidom, datetime, operator, pickle, sys
from xml.dom.minidom import parse
startTime = datetime.datetime.now()
##args = sys.argv
path = "C:/Users/courtney.zelinsky/Desktop/deid"

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

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

docCount=0
docs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml' , os.listdir(path))

allData = {}
truePosCount = 0
falseNegCount = 0
falsePosCount = 0

for doc in docs:
    if not doc.endswith('.out.xml'):
        docCount += 1
        print "\n\n_______________________________________\n"
        print "Now parsing document %s out of %s..." % (docCount, len(docs)/2)
        print "_______________________________________\n\n"
        parsedGSDoc = parse(path + '\\' + doc)
        parsedEngineDoc = parse(findPair(path + '\\' + doc))                   
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

        gsDic = dict(zip(gsEntryNumsGroupedTuple, gsCodes))
        # if an entry number appears twice (if the gold standard isn't perfect + has overlapping entries),
        #  i'll need to create a test for the engine output later
        # gsDic1[entry] = gsWorkingData[i][1]
        # which looks like {'entry_217' : 'DATE', 'entry_216': 'DATE', 'entry_36': 'DATE', 'entry_274': 'LAST_NAME' ...}

        contentNodes = parsedGSDoc.getElementsByTagName('content')
        for node in contentNodes:
            text = node.childNodes
            for node in text:
                if node.parentNode.getAttribute('ID') in gsDic1:
                    gsDic2[node.parentNode.getAttribute('ID')] = node.data
        # {u'entry_202': u'January', u'entry_203': u'2012.', u'entry_303': u"Jude's", u'entry_302': u'St.'...}
        
        ##for entry in gsEntryNumsOnly:
        ##    for i in range(len(gsWorkingData)):
        ##      if entry in gsWorkingData[i][0] and entry in gsDic2:
        ##          finalGSDic[entry] = ((gsWorkingData[i][1], gsDic2[entry]))

        # Don't really even need this if I can get the xpath module working ^^^


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

        engDic = dict(zip(engineEntryNumsGroupedTuple, engineCodes))

        ##
        ## Begin comparison of data structures
        ##

        #
        # True Positives
        #
        truePositives = {x:gsDic[x] for x in gsDic if x in engDic}
        print "True Positives: (x%s found!)\n" % len(truePositives)
        truePosCount += len(truePositives)
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
        falseNegCount += len(gsDiffs)
        print gsDiffs
        print ""
        print "In engine version but not in gold standard version (false positives): (x%s found)" % len(engineDiffs)
        falsePosCount += len(engineDiffs)
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

        print "\n\nScope Match - Value Mismatch MIMs:"
        print "_____________________________________________\n"

        scopeMatchValueMismatch = []
        for i in range(len(engineDiffsList)):
            for j in range(len(gsWorkingData)):
                if engineDiffsList[i][0] == gsWorkingData[j][0]:
                    print engineDiffsList[i][1] + " was confused for the correct mim code " + gsWorkingData[j][1]
                    scopeMatchValueMismatch.append(gsWorkingData[j][0])    

        print "x%s mismatch instance(s) of proper scope but incorrect value involving entry number(s):\n" % len(scopeMatchValueMismatch)
        print scopeMatchValueMismatch
        print "\n"

        outputList = []
        documentText = {}

        scopeMatchValueMismatchEntryNums = [entryNum for entryNum in scopeMatchValueMismatch]
        entryJustNumsList = []
        for entry in scopeMatchValueMismatchEntryNums:
            for subentry in entry:
                entryJustNumsList.append(subentry.split("_")[1])

        for node in contentNodes:
            text = node.childNodes
            for node in text:
                documentText[node.parentNode.getAttribute('ID')] = node.data


        # Checking for scope mismatch, value match (Overlapping entry numbers, same code value)
        #
        # Test cases: "in October" vs "October" for DATE, "on October 21 1993" and "October 21 1993" as ABSOLUTE_DATE
        # --> entry is in tuple but engine result tuple and gs tuple are different lengths

        print "\n\nScope Mismatch - Value Match MIMs:"
        print "_____________________________________________\n"

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

print 'Took', datetime.datetime.now()-startTime, 'to run %s files.\n\n' % (len(docs)/2)

print 'Totals'
print 'True Positives: ' + str(truePosCount)
print 'False Negatives: ' + str(falseNegCount)
print 'False Positives: ' + str(falsePosCount)










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

vals = ['LAST_NAME', 'MALE_NAME', 'FEMALE_NAME', 'PHONE_NUMBER', 'MEDICAL_RECORD_NUMBER', 'ABSOLUTE_DATE', 'DATE',
        'ADDRESS', 'LOCATION', 'AGE', 'SOCIAL_SECURITY_NUMBER', 'CERTIFICATE_OR_LICENSE_NUMBER', 'ID_OR_OTHER_CODE',
        'NAME', 'ORGANIZATION', 'URL', 'E_MAIL_ADDRESS', 'TIME', 'OTHER']
 
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

    out.write("""       <table>
                            <tr>
                                <td></td>
                                <td></td>
                                <th colspan="5" style="border:1px solid black">Predicted (eng)<p><img src="http://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/U%2B2192.svg/25px-U%2B2192.svg.png"></p></th>
                            </tr>
                            <tr style="border:1px solid black">
                                <th style="border:1px solid black; width:60px;">
                                    <div class="vertical-text">
                                        <div class="vertical-text__inner"><th rowspan="5">Actual (gs)<p><img src="http://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/U%2B2190.svg/25px-U%2B2190.svg.png"></p></th></div>
                                    </div>
                                </th>""")
    out.write('<th style="border:1px solid black">' + '</th><th style="border:1px solid black">'.join(vals) +
              """</th><th style="border:1px solid black">Sum</th><th style="border:1px solid black">Micro-recall</th></tr>""")
    out.write('<tr></tr><tr></tr>')
    out.write("""
                        </table>
                    </div>
                    <p style="text-align:center; font-size:12px"> Email cmzelinsky@gmail.com for questions / comments / suggestions for this script </p>
                </body>
            </html> """)
    
##    out.write('<tr><td><div id="container">')
##    out.write('<table style="border:1px solid black"><tr style="border:1px solid black"><td></td><th colspan="3" style="border:1px solid black">Predicted (Engine Output)</th></tr></td></tr>')
##    out.write('<tr style="border:1px solid black"><td></td><td style="border:1px solid black"></td><td style="border:1px solid black">1</td><td style="border:1px solid black">0</td></tr>')
##    out.write('<tr style="border:1px solid black"><th><div class="vertical-text"><div class="vertical-text__inner">Actual (Gold Standards)</div></div></th>')
##    out.write('<td style="border:1px solid black">1</td><td id="numbers" style="border:1px solid black">True Positives</td><td id="numbers" style="border:1px solid black">False Negatives</td></tr>')
##    out.write('<tr style="border:1px solid black"><td></td><td id="numbers" style="border: 1px solid black">0</td><td id="numbers" style="border:1px solid black">False Postives</td><td style="border:1px solid black">True Negatives</td></tr>')
##    out.write('</table></div></td></tr></table>')
##    out.write('<table><tr><th><div class="vertical-text"><div class="vertical-text__inner">First th</div></div></th><td>Some cell</td><td>And another</td></tr><tr><th><div class="vertical-text"><div class="vertical-text__inner">Second th</div></div></th><td>12</td>')
##    out.write('<td>12314</td></tr><tr><th><div class="vertical-text"><div class="vertical-text__inner">Third th</div></div></th><td>12</td><td>12314</td></tr></table></div>')
##    out.write('<p style="text-align:center; font-size:12px"> Email courtney.zelinsky@mmodal.com for questions / comments / suggestions for this script </p>')
##    out.write('</body></html>')


###'D': ['LAST_NAME', 'MALE_NAME', 'FEMALE_NAME', 'PHONE_NUMBER', 'MEDICAL_RECORD_NUMBER', 'ABSOLUTE_DATE', 'DATE', 'ADDRESS', 'LOCATION', 'AGE', 'SOCIAL_SECURITY_NUMBER', 'CERTIFICATE_OR_LICENSE_NUMBER', 'ID_OR_OTHER_CODE', 'NAME', 'ORGANIZATION', 'URL', 'E_MAIL_ADDRESS', 'TIME', 'OTHER'] ###
