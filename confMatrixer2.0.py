# -*- coding: utf-8 -*-
## author : Courtney Zelinsky
## created : 5/13/14
##
## to run:
## Call on cmd line with arg[1] = path containing all files for testing, arg[2] = D, T, S, or C to initialize test type (Deid, Temporality, Subject, or Certainty)
## Please have gold standard files in the format ~.xml and their engine counterparts as ~.out.xml
##

import os, datetime, sys, re, timeit
import pandas
import numpy
from xml.dom.minidom import parse
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from lxml import etree

startTime = datetime.datetime.now()
print startTime

# path = sys.argv[1]
path = "C:\\Users\\courtney.zelinsky\\Desktop\\temporalityTestingSub"

#modifierType = sys.argv[2]
modifierType = 'D'

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

gsRows = {}
gsList = []
engList = []
overlaps = []

matrix = pandas.DataFrame(index=labels[modifierType], columns=labels[modifierType])
matrix = matrix.fillna(0)

# How the matrix works:

# 1) True positives are counted based on same scoping and partial scoping matches.
# 2) False positives to be displayed in the confusion matrix can only come from mims
#    identified as having at least comprobable scoping but a mismatched label.


##
## Classes
##

class TElement(ET._Element):
    """
    Extending elementtree's Element class so as to accommodate text
    """
    def __init__(self, tag, style=None, text=None, tail=None, parent=None, attrib={}, **extra):
        ET._Element.__init__(self, tag, dict(attrib, **extra))
        if text:
            self.text = text
        if tail:
            self.tail = tail
        if style:
            self.style = style
        if parent is not None:
            parent.append(self)

##
## Functions
##

def find_pair(fname):
    """
    Find engine output version of annotated gold standard document
    """

    return fname[:-3] + 'out.xml'

def get_overlaps(gsList, engList):

    for gsRow in gsList:
        for engRow in engList:
            # If the "middle" token (the list[len(list)/2] token) from a gold entries list is in the engine tokens' entries, it's an overlap
            if gsRow['Entries'][len(gsRow['Entries'])/2] in engRow['Entries'] and engRow['Document'] == gsRow['Document']:
                overlaps.append({'Document': engRow['Document'], 'gsEntries': list(gsRow['Entries']), 'engEntries': list(engRow['Entries']), 'gsLabel': gsRow['Label'], 'engLabel': engRow['Label']})


def mims_to_dicts(goldDocs):
    """Establish gold standard data structures

    Maps tokens-to-label mapping to the respective document

    e.g. gsDic['ClinicalDocument...'] =
            {('entry_10', 'entry_11') : (u'CERTAIN',), ('entry_100',) : (u'MAYBE',), ... }
    """

    def process_entries(entries):

        mimChildren = []

        for entry in entries:
            mimChildren.append(entry.firstChild)

        for child in mimChildren:
            bindings = child.getElementsByTagNameNS('*', 'narrativeBinding')
            entries = sorted(binding.getAttribute('ref').split('_')[1] for binding in bindings)
            codeLabels = child.getElementsByTagNameNS('*', 'code')
            label = [child.getAttribute('code') for child in codeLabels if child.getAttribute('code') != '\\' and child.getAttribute('displayName') != "Lifelong"]
            if mode == 'gs':
                gsList.append({'Document': doc, 'Entries': entries, 'Label': label[0]})
                #gsList.append(['Document':doc, 'Entries': tuple(entries), 'Label': label, 'Tokens': tuple(tokens)})
            elif mode == 'eng':
                engList.append({'Document': doc, 'Entries': set(entries), 'Label': label[0]})
                #engList.append(['Document': doc, 'Entries': tuple(entries), 'Label': label, 'Tokens': tuple(tokens)})


    for doc in goldDocs:
        mode = "gs"
        goldEntries = parse(os.path.join(path, doc)).getElementsByTagName('entry')
        process_entries(goldEntries)

        mode = "eng"
        engEntries = parse(os.path.join(path, find_pair(doc))).getElementsByTagName('entry')
        process_entries(engEntries)


def data_to_matrix(tp):

    """Add data to a DataFrame matrix.

        e.g.
                        PAST  RECENTPAST  FUTURE  PRESENT  UNDEFINED
        PAST           38          0       0        34         0
        RECENTPAST     0           56      0        2          1
        FUTURE         0           0       9        0          2
        PRESENT        12          2       0        4          0
        UNDEFINED      0           0       0        0          6

    """

    #Add true positive data to matrix
    for row in tp:
        matrix.loc[row['Label'], row['Label']] += 1

#######################################################################################################################

print "Start time: ", startTime

# gsList and engList = lists of "dictionary-rows" used to create base dataframes

goldDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) != 'out', os.listdir(path))

mims_to_dicts(goldDocs)

print "gsList: ", gsList
print "engList: ", engList

get_overlaps(gsList, engList)

allMims = gsList.extend(engList)

gsTups = [tuple(r.items()) for r in gsList]
engTups = [tuple(r.items()) for r in engList]


print "gsTups: ", gsTups
print "engTups: ", engTups

# Base DataFrames
# gsData = pandas.DataFrame(gsList)
# engData = pandas.DataFrame(engList)
# allData = pandas.DataFrame(allMims)

# True Positives

# --Complete Overlaps
# More useful to engines like Deid, in which the scoping between gold and engine mims is the exact same much more often.
# Not so much for Temporality, for instance.
truePosTups = []
for row in gsTups:
    i = 0
    found = False
    while i < len(engTups) and not found:
        if row == engTups[i]:
            found = True
            truePosTups.append(row)
        else:
            i+=1

# --1-token Overlaps
#print "Overlaps: ", overlaps
o = pandas.DataFrame(overlaps)
#print "\n\nOverlaps\n", o
#o.to_csv('testOverlaps.csv', sep="\t")

# True Positive Total:
truePos = [dict(row) for row in truePosTups]
#print "truePos: ", truePos
tpData = pandas.DataFrame(truePos)
#print "\n\n[True Positive Data]\n", tpData

# False Negatives
falseNeg = [dataRow for dataRow in gsList if dataRow not in engList]
fnData = pandas.DataFrame(falseNeg)
#print "\n\n[False Negative Data]\n", fnData

# False Positives
#
# falsePos = [dataRow for dataRow in engList if dataRow not in gsList]
# FalsePositives = FalsePositives - PartialOverlaps
# fpData = pandas.DataFrame(falsePos)
# print "\n\n[False Positive Data]\n", fpData

data_to_matrix(truePos)

print "\n\n", matrix

# print "Initializing dicts: ", timeit.timeit("initialize_dicts()", setup="from __main__ import initialize_dicts")
# timeit -- 801.550652967 on full temporalityTesting set with confMatrix init

# print  "Mims to dicts: ", timeit.timeit("mims_to_dict()", setup="from __main__ import mims_to_dict")


print "\n\nTook ", datetime.datetime.now()-startTime, " to run ", len(goldDocs), " files."
#print len(gsData.index), " mims in gold data"
print len(gsList), " mims in gold data"
#print len(engData.index), " mims in engine data"
print len(engList), " mims in eng data"