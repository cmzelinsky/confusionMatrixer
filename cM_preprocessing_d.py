from xml.dom.minidom import parse
import os, datetime, sys, re, codecs
from collections import namedtuple
import difflib

startTime = datetime.datetime.now()
print startTime

# path = sys.argv[1]
path = "C:\\Users\\courtney.zelinsky\\Desktop\\temporalityTesting"


#modifierType = sys.argv[2]
modifierType = 'T'

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

##
## Variables
##

goldDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) != 'out' and str(x.split('.')[len(x.split('.'))-1]) == 'xml', os.listdir(path))

engMims = {}
gsMims = {}

truePos = {}
mismatchFp = {}
spontFp = {}
falseNeg = {}

texts = {}

remapping = False

Mim = namedtuple("Mim", "entries, tokens, label")

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

##
## Functions
##

def is_namedtuple_instance(x):
    t = type(x)
    b = t.__bases__
    if len(b) != 1 or b[0] != tuple:
        return False
    f = getattr(t, '_fields', None)
    if not isinstance(f, tuple):
        return False
    return all(type(n)==str for n in f)


def binary_search(eng_li, gs_li, key, i_min, i_max):
    if i_max < i_min:
        return gs_li
    else:
            i_mid = (i_min + i_max)/2

            if key in eng_li[i_mid].entries:
                return i_mid
            elif sorted(list(eng_li[i_mid].entries))[-1] > key:
                return binary_search(eng_li, gs_li, key, i_min, i_mid-1)
            elif sorted(list(eng_li[i_mid].entries))[0] < key:
                return binary_search(eng_li, gs_li, key, i_mid+1, i_max)


def find_pair(fname):
    return fname[:-3] + 'out.xml'


def process_entries(entries):
        mimChildren = [entry.firstChild for entry in entries if (entry.firstChild.localName == 'scope' or entry.firstChild.localName == 'term')]

        for child in mimChildren:
            entries = sorted(int(binding.getAttribute('ref').split('_')[1]) for binding in child.getElementsByTagNameNS('*', 'narrativeBinding'))
            label = [child.getAttribute('code') for child in child.getElementsByTagNameNS('*', 'code') if child.getAttribute('code') != '\\' and child.getAttribute('displayName') != "Lifelong"][0]
            if mode == 'gs' and len(entries) > 0 and label in labels[modifierType]:
                if remapping is True:
                    if label == 'RECENTPAST':
                        gsMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], 'PAST'))
                    elif label == 'FUTURE':
                        gsMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], 'PRESENT'))
                    else:
                        gsMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
                else:
                    gsMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
            elif mode == 'eng' and len(entries) > 0 and label in labels[modifierType]:
                engMims[doc].append(Mim(set(entries), [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
            del entries
            del label

        del mimChildren

#######################################################################################################################

for doc in goldDocs:
    texts[doc] = {}
    goldParsed = parse(os.path.join(path, doc))
    for contentNode in goldParsed.getElementsByTagNameNS('*', 'content'):
        getTokenization = int(contentNode.getAttribute('ID').split('_')[1])
        texts[doc][getTokenization] = contentNode.firstChild.nodeValue

    mode = "gs"
    gsMims[doc] = []
    process_entries(goldParsed.getElementsByTagName('entry'))

    mode = "eng"
    engMims[doc] = []
    process_entries(parse(os.path.join(path, find_pair(doc))).getElementsByTagName('entry'))

    i = 0
    while i < len(gsMims[doc]):
        # index of list at which there is a match in scope between gold and eng mims
        # that is to say, the results of this loop will either be identification of true positives or fp mismatches

        # returns index at which there is an overlap in scope between a GS and ENG mim
        match = binary_search(engMims[doc], gsMims[doc][i], gsMims[doc][i].entries[0], 0, len(engMims[doc])-1)

        if is_namedtuple_instance(match):
            if not doc in falseNeg:
                falseNeg[doc] = []
            falseNeg[doc].append(match)
        elif type(match) == int:
            # print match
            # print difflib.SequenceMatcher(None, list(gsMims[doc][i].entries), list(engMims[doc][match].entries)).ratio()
            if difflib.SequenceMatcher(None, gsMims[doc][i].tokens, engMims[doc][match].tokens).ratio() > .6:
                if gsMims[doc][i].label == engMims[doc][match].label:
                    if doc not in truePos:
                        truePos[doc] = []
                    truePos[doc].append(engMims[doc][match])
                elif gsMims[doc][i].label != engMims[doc][match].label:
                    if doc not in mismatchFp:
                        mismatchFp[doc] = []
                    mismatchFp[doc].append(engMims[doc][match])
            else:
                # not catching everything here -- need mims not caught by binary search also
                if doc not in spontFp:
                    spontFp[doc] = []
                spontFp[doc].append(engMims[doc][match])
        i += 1

print gsMims['ClinicalDocument_2202830448.xml']
print engMims['ClinicalDocument_2202830448.xml']
print "\n\n"
print truePos['ClinicalDocument_2202830448.xml']
print falseNeg['ClinicalDocument_2202830448.xml']
print spontFp['ClinicalDocument_2202830448.xml']


# Quick Testing

if Mim(entries=set([545, 546, 547, 548, 549, 550, 551]), tokens=[u'history ', u'of ', u'any ', u'alcohol ', u'or ', u'drug ', u'abuse. '], label=u'PAST') in truePos['ClinicalDocument_2202830448.xml']:
    print "1 -True"
if Mim(entries=set([662, 663, 664, 665, 666, 667]), tokens=[u'The ', u"patient's ", u'parents ', u'have ', u'passed ', u'away '], label=u'PAST') in falseNeg['ClinicalDocument_2202830448.xml']:
    print "2 -True"
if Mim(entries=set([1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416]), tokens=[u'last ', u'2D ', u'echocardiogram ', u'to ', u'look ', u'for ', u'any ', u'other ', u'explanation ', u'for ', u'his ', u'atrial ', u'fibrillation. '], label=u'PAST') in spontFp['ClinicalDocument_2202830448.xml']:
    print "3 -True"
#Mim(entries=[], tokens=[], label='') in mismatchFp['ClinicalDocument_2202830448.xml']

print "\n\nTook ", datetime.datetime.now()-startTime, " to run ", len(goldDocs), " files."