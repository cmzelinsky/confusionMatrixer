# -*- coding: utf-8 -*-
## author : Courtney Zelinsky
## created : 5/13/14
##
## to run:
## Call on cmd line with arg[1] = path containing all files for testing
## Please have gold standard files in the format ~.xml and their engine counterparts as ~.out.xml
##

import os, datetime, sys, re, timeit, matplotlib
import pandas
import numpy
from xml.dom.minidom import parse
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from lxml import etree

startTime = datetime.datetime.now()
print startTime

# path = sys.argv[1]
path = "C:\\Users\\courtney.zelinsky\\Desktop\\temporalityTesting"

#modifierType = sys.argv[2]
modifierType = 'T'

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

# Variables

gsList = []
engList = []

# Classes

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

# Functions

def find_pair(fname):
    """
    Find engine output version of annotated gold standard document
    """

    return fname[:-3] + 'out.xml'

def mims_to_dicts(goldDocs):
    """Establish gold standard data structures

    Maps tokens-to-label mapping to the respective document

    e.g. gsDic['ClinicalDocument...'] =
            {('entry_10', 'entry_11') : (u'CERTAIN',), ('entry_100',) : (u'MAYBE',), ... }
            """

    def process_entries(entries):

        children = []

        for entry in entries:
            childNodes = filter(lambda x: x.localName == 'binding', entry.firstChild.childNodes)
            children.extend(childNodes)

        for child in children:
            bindings = []
            bindings.extend([bindingNode.getAttribute('ref') for bindingNode in child.childNodes if bindingNode.localName == "narrativeBinding"])
            entries = tuple(sorted(str(binding) for binding in bindings if len(binding) > 0))
            # Turning off capturing Lifelongs
            label = [child.getAttribute('code') for child in entry.firstChild.childNodes if (child.localName == 'code' and child.getAttribute('code') != '\\' and child.getAttribute('displayName') != "Lifelong")]
            label.extend([child.getAttribute('displayName') for child in entry.firstChild.childNodes if (child.localName == 'code' and child.getAttribute('code') == '\\')])
            if len(entries) == 0:
                continue
            else:
                if mode == 'gs':
                    gsList.append({'Document': doc, 'Entries': tuple(entries), 'Label': label})
                elif mode == 'eng':
                    engList.append({'Document': doc, 'Entries': tuple(entries), 'Label': label})


    for doc in goldDocs:
        mode = "gs"
        goldEntries = parse(os.path.join(path, doc)).getElementsByTagName('entry')
        process_entries(goldEntries)

        mode = "eng"
        engEntries = parse(os.path.join(path, find_pair(doc))).getElementsByTagName('entry')
        process_entries(engEntries)


#######################################################################################################################

print "Start time: ", startTime


allDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml', os.listdir(path))
engDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) == 'out', os.listdir(path))
goldDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) != 'out', os.listdir(path))

mims_to_dicts(goldDocs)

gsData = pandas.DataFrame(gsList)
engData = pandas.DataFrame(engList)

print gsData
print "\n\n\n"
print engData

gsData.to_csv('gsData.csv', sep="\t")
engData.to_csv('engData.csv', sep="\t")

truePos = gsData.reindex(gsData.index.intersection(engData.index))

print truePos.head()
print truePos.tail()

print "Took ", datetime.datetime.now()-startTime, " to run ", len(goldDocs), " files."