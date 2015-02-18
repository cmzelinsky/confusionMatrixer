# -*- coding: utf-8 -*-
# author : Courtney Zelinsky
# created : 5/13/14
# last modified: 2/5/15

# To run:
# Call on cmd line with arg[1] = path containing all files for testing, arg[2] = D, T, S, or C to initialize test type (Deid, Temporality, Subject, or Certainty)
# Please have gold standard files in the format ~.xml and their engine counterparts as ~.out.xml

# How the matrix works:

# 1) True positives are counted based on same scoping and partial scoping matches.
# 2) False positives to be displayed in the confusion matrix can only come from mims
#    identified as having at least comprobable scoping but a mismatched label.

from __future__ import division
import os, datetime, sys, re, codecs
import sqlite3, csv
import pandas
#import numpy
from xml.dom.minidom import parse
from lxml import etree

startTime = datetime.datetime.now()
print startTime

# path = sys.argv[1]
path = "C:\\Users\\courtney.zelinsky\\Desktop\\temporalityTestingSub"
#

#modifierType = sys.argv[2]
modifierType = 'T'

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

##
## Variables
##

# allDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml', os.listdir(path))
# engDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) == 'out', os.listdir(path))

labels = {
        "S":[u'SUBJECT', u'PROVIDER', u'AUTHOR', u'BABY', u'NONFAMILY', u'FAMILY', u'SIBLING', u'MOTHER', u'FATHER',\
          u'AUNT', u'UNCLE', u'GRANDPARENT', u'CHILD'],
        "C": [u'MAYBE', u'CERTAIN', u'HEDGED', u'HYPOTHETICAL', u'RULED_OUT'\
        , u'NEGATED'],
        "D": [u'LAST_NAME', u'MALE_NAME', u'FEMALE_NAME', u'PHONE_NUMBER', u'MEDICAL_RECORD_NUMBER',\
          u'ABSOLUTE_DATE', u'DATE', u'ADDRESS', u'LOCATION', u'AGE', u'SOCIAL_SECURITY_NUMBER',\
          u'CERTIFICATE_OR_LICENSE_NUMBER', u'ID_OR_CODE_NUMBER', u'NAME', u'ORGANIZATION', u'URL', u'E_MAIL_ADDRESS',\
          u'TIME', u'OTHER', u'HOSPITAL', u'INITIAL', u'HOSPITAL_SUB'],
        "T": [u'PAST', u'RECENTPAST', u'FUTURE', u'PRESENT', u'UNDEFINED'],
        "i2b2":[u'NEGATED'],
        }

texts = {}

gsRows = {}
gsList = []
engList = []

truePos = []
falsePos = []
overlaps = []

# db = sqlite3.connect('confusionData.db')
# confusionDataDb = db.cursor()


matrix = pandas.DataFrame(index=labels[modifierType], columns=labels[modifierType])
matrix = matrix.fillna(0)


##
## Functions
##

def find_pair(fname):
    """
    Find engine output version of annotated gold standard document
    """

    return fname[:-3] + 'out.xml'


def get_tp_fp_html(gsList, engList):

    for gsRow in gsList:
        engListByDoc = filter(lambda x: x['Document'] == gsRow['Document'], engList)
        if not engListByDoc:
            continue
        else:
            j = 0
            found = False
            while j < len(engListByDoc) and not found:
                document = engListByDoc[j]['Document']
                print document
                label = engListByDoc[j]['Label']
                engEntries = sorted(list(engListByDoc[j]['Entries']))
                # If the "middle" token (the list[len(list)/2] token) from a gold entries list is in the engine tokens' entries, it's an overlap
                if ((gsRow['Entries'][0] or gsRow['Entries'][-1]) in engEntries) and document == gsRow['Document']:
                    # Mim has overlap and matches label -- goes to confMatrix
                    if label == gsRow['Label']:
                        found = True
                        truePos.append({'Document': document,\
                                        'engEntries': engEntries,\
                                        'Label': label,})
                                        #'context': texts[document]})
                    # Mim has overlap and is a label mismatch -- goes to confMatrix
                    elif label != gsRow['Label']:
                        found = True
                        gsEntries = gsRow['Entries']
                        gsLabel = gsRow['Label']
                        falsePos.append({'Document': document,\
                                         'gsEntries': gsEntries, \
                                         'engEntries': engEntries,\
                                         'gsLabel': gsLabel, \
                                         'engLabel': label})
                                         # 'context': texts[document]})
                        outHtml = gsLabel + "_x_" + label + ".html"
                        with codecs.open(os.path.join(path, outHtml), 'a', 'utf-8') as outDoc:
                            content = texts[document][:engEntries[0]] + '<font style="background-color:yellow;"><strong>'.split() + texts[document][engEntries[0]:engEntries[-1]] + '</strong></font>'.split() + texts[document][engEntries[-1]:]
                            #content = content[:gsEntries[0]] + '<font style="background-color:green;><strong>'.split() + content[gsEntries[0]:gsEntries[-1]] + '</strong></font>'.split() + content[gsEntries[-1]:]
                            if outHtml not in os.listdir(path):
                                outDoc.write("""
                                <html>
                                    <head>
                                        <title>""" + gsLabel + """ confusions as """ + label + """</title>
                                    </head>
                                    <body>
                                        <h1>""" + gsLabel + """ confusions as """ + label + """ </h1>
                                            <table>
                                                <tr>
                                                    <th>""" + document + """</th>
                                                    <td>""" + ' '.join(content) + """</td>
                                                </tr>
                                """)
                            else:
                                outDoc.write("""
                                <tr>
                                    <th>""" + document + """</th>
                                    <td>""" + ' '.join(content) + """</td>
                                </tr>""")

                    # MIM not in gold standard at all -- garbage produced by engine
                    # elif ((gsRow['Entries'][0] or gsRow['Entries][-1]']) not in engListByDoc[j]['Entries']) and engListByDoc[j]['Document'] == gsRow['Document']:
                    #    falsePos.append({'Document': engListByDoc[j]['Document'], 'engEntries': list(engListByDoc[j]['Entries']), 'engLabel': engListByDoc[j]['Label']})
                j+=1

def mims_and_text_to_dicts(goldDocs, remapping):
    """Establish gold standard data structures

    Maps tokens-to-label mapping to the respective document

    e.g. gsDic['ClinicalDocument...'] =
            {('entry_10', 'entry_11') : (u'CERTAIN',), ('entry_100',) : (u'MAYBE',), ... }
    """

    def process_entries(entries):

        mimChildren = []

        for entry in entries:
            if entry.firstChild.localName != 'scope':
                print entry.firstChild.localName
                continue
            else:
                mimChildren.append(entry.firstChild)

        for child in mimChildren:
            bindings = child.getElementsByTagNameNS('*', 'narrativeBinding')
            entries = sorted(int(binding.getAttribute('ref').split('_')[1]) for binding in bindings)
            codeLabels = child.getElementsByTagNameNS('*', 'code')
            label = [child.getAttribute('code') for child in codeLabels if child.getAttribute('code') != '\\' and child.getAttribute('displayName') != "Lifelong"]
            label = label[0]
            if mode == 'gs' and len(entries) > 0:
                if remapping is True:
                    if label == 'RECENTPAST':
                        gsList.append({'Document': doc, 'Entries': entries, 'Label': 'PAST'})
                    elif label == 'FUTURE':
                        gsList.append({'Document':doc, 'Entries': entries, 'Label': 'PRESENT'})
                    else:
                        gsList.append({'Document': doc, 'Entries': entries, 'Label': label})
                else:
                    gsList.append({'Document': doc, 'Entries': entries, 'Label': label})
                #gsList.append(['Document':doc, 'Entries': tuple(entries), 'Label': label, 'Tokens': tuple(tokens)})
            elif mode == 'eng' and len(entries) > 0:
                engList.append({'Document': doc, 'Entries': set(entries), 'Label': label})
                #engList.append(['Document': doc, 'Entries': tuple(entries), 'Label': label, 'Tokens': tuple(tokens)})


    for doc in goldDocs:
        goldParsed = parse(os.path.join(path, doc))
        texts[doc] = [contentNode.firstChild.nodeValue for contentNode in goldParsed.getElementsByTagName('content')]

        mode = "gs"
        process_entries(goldParsed.getElementsByTagName('entry'))

        mode = "eng"
        engEntries = parse(os.path.join(path, find_pair(doc))).getElementsByTagName('entry')
        process_entries(engEntries)


def data_to_matrix(tp, fp):

    """Add data to a DataFrame matrix.

        e.g.
                        PAST  RECENTPAST  FUTURE  PRESENT  UNDEFINED
        PAST           38          0       0        34         0
        RECENTPAST     0           56      0        2          1
        FUTURE         0           0       9        0          2
        PRESENT        12          2       0        4          0
        UNDEFINED      0           0       0        0          0

    """

    #Add true positive data to matrix
    for row in tp:
        matrix.loc[row['Label'], row['Label']] += 1

    for row in fp:
        matrix.loc[row['gsLabel'], row['engLabel']] += 1


def finish_htmls():
    for html in filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'html', os.listdir(path)):
        with codecs.open(os.path.join(path, html), 'w', 'utf-8') as out:
            out.write("""</table></body></html>""")
        out.close()

#######################################################################################################################

print "Start time: ", startTime

# gsList and engList = lists of "dictionary-rows" used to create base dataframes

goldDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) != 'out' and str(x.split('.')[len(x.split('.'))-1]) == 'xml', os.listdir(path))

# Turn on or off remapping to map gold only categories like "RECENTPAST" and "FUTURE" to "PAST" and "PRESENT" respectively
mims_and_text_to_dicts(goldDocs, remapping=True)

print "gsList: ", gsList[:3]
print "engList: ", engList[:3]

get_tp_fp_html(gsList, engList)
#finish_htmls()

allMims = gsList.extend(engList)

# True Positives

# True Positive Total:
print "truePos: ", truePos[:10]
#print "truePos: ", truePos
#tpData = pandas.DataFrame(truePos)
#print "\n\n[True Positive Data]\n", tpData

# False Negatives
falseNeg = [dataRow for dataRow in gsList if dataRow not in engList]
#fnData = pandas.DataFrame(falseNeg)
print "\n\n[False Negative Data]\n", falseNeg[:5]
print "total FNs: ", len(falseNeg)

# False Positives
# FalsePositives = FalsePositives - PartialOverlaps
#fpData = pandas.DataFrame(falsePos)
print "\n\n[False Positive Data]\n", falsePos[:5]
print "total FPs: ", len(falsePos)
#fpData.to_csv('fp.csv', sep="\t")

data_to_matrix(truePos, falsePos)

print "\n\n", "v Gold\t\t> Engine\n", matrix

print '\n\nPrecision (TP/TP+FP): ', len(truePos)/(len(truePos)+len(falsePos))
print 'Recall (TP/TP+FN): ',  len(truePos)/(len(truePos)+len(falseNeg))

print "\n\nTook ", datetime.datetime.now()-startTime, " to run ", len(goldDocs), " files."
#print len(gsData.index), " mims in gold data"
print len(gsList), " mims in gold data"
#print len(engData.index), " mims in engine data"
print len(engList), " mims in eng data"


################################################################# Junk

# Base DataFrames
# gsData = pandas.DataFrame(gsList)
# engData = pandas.DataFrame(engList)
# allData = pandas.DataFrame(allMims)

# confusionDataDb.execute("CREATE TABLE fp (document, gsEntries, engEntries, gsLabel, engLabel;")
# with open('fp.csv', 'rb') as fpCSV:
#     dictReader = csv.DictReader(fpCSV)
#     toDb = [(i['document'], i['gsEntries'], i['engEntries'], i['gsLabel'], i['engLabel']) for i in dictReader]
#
# confusionDataDb.executemany("INSERT INTO fp (document, gsEntries, engEntries, gsLabel, engLabel) VALUES (?, ?, ?, ?, ?);", toDb)
# db.commit()

# --Complete Overlaps
# More useful to engines like Deid, in which the scoping between gold and engine mims is the exact same much more often.
# Not so much for Temporality, for instance.
# gsTups = [tuple(r.items()) for r in gsList]
# engTups = [tuple(r.items()) for r in engList]
# truePosTups = []
# for row in gsTups:
#     i = 0
#     found = False
#     while i < len(engTups) and not found:
#         if row == engTups[i]:
#             found = True
#             truePosTups.append(row)
#         else:
#             i+=1