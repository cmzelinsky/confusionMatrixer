from xml.dom.minidom import parse
import os, datetime, sys, re
from operator import attrgetter
from collections import namedtuple
import difflib
import numpy
import pandas
import xml.etree.ElementTree as ET
from IPython.display import HTML

######################################################################################################################
##
## Confusion Matrixer for Modifiers and Deid... v2
##
## - Tested on Python 2.7
## - Document tokenization with gaps now handled
## - Much quicker on huge sets (tested up to 1000 gold + 1000 eng docs)
## - Mim overlap is hinged on a phrase similarity ratio, adjustable around line 270
## - Tested on Temporality, ... should hypothetically work with any engine,
##      just need to catch the respective mim type (ln 3 of process_entries())

startTime = datetime.datetime.now()
print startTime

# path = sys.argv[1]
# path = "C:\\Users\\courtney.zelinsky\\Desktop\\temporalityTestingSub"
path = "C:\\Users\\courtney.zelinsky\\Desktop\\chapmanCorpus"

#modifierType = sys.argv[2]
#modifierType = 'T'
modifierType = 'i2b2'

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

##
## Variables
##

goldDocs = filter(lambda x: str(x.split('.')[len(x.split('.'))-2]) != 'out' and \
                            str(x.split('.')[len(x.split('.'))-1]) == 'xml', os.listdir(path))

engMims = {}
gsMims = {}

truePos = {}
mismatchFp = {}
spontFp = {}
falseNeg = {}

tpFlat = []
fnFlat = []
mismatchFlat = []

confusions = {}
texts = {}

remapping = True

Mim = namedtuple("Mim", "entries, tokens, label")
mismatchMim = namedtuple("mismatchMim", "doc, gsEntries, engEntries, gsTokens, engTokens, gsLabel, engLabel, context")
fnMim = namedtuple("fnMim", "doc, entries, tokens, gsLabel, context")

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
        "i2b2":[u'NEGATIVE'],
        }

labelsTup = [(label1, label2) for label1 in labels[modifierType] for label2 in labels[modifierType]]

matrix = pandas.DataFrame(index=labels[modifierType], \
                          columns=labels[modifierType]+['totals', 'fn', 'tp', 'precision', 'recall', 'f-score'])
matrix = matrix.fillna(0)
pandas.set_option('display.max_columns', 1000)

##
## Functions
##

def merge_sequences_get_context(gsEntries, engEntries, doc):
    # Take in entries lists, merge them, add 10 in range (or less) on either side, output the full concordance

    # Extended from:
    # http://stackoverflow.com/questions/14241320/interleave-different-
    # length-lists-elimating-duplicates-and-preserve-order-in-py

    sm = difflib.SequenceMatcher(a=gsEntries,b=engEntries)
    res = []
    for (op, gsStart, gsEnd, engStart, engEnd) in sm.get_opcodes():
        if op == 'equal' or op == 'delete':
            #Range appears in both sequences, or only in the first one.
            res += gsEntries[gsStart:gsEnd]
        elif op == 'insert':
            #Range appears in only the second sequence.
            res += engEntries[engStart:engEnd]
        elif op == 'replace':
            #There are different ranges in each sequence - add both.
            res += gsEntries[gsStart:gsEnd]
            res += engEntries[engStart:engEnd]

    # checking if +/-10 tokens is out of scope to pull concordance
    if res[0]-10 < 0:
        #if res[0]-10 not in texts[doc]: no, bad logic -- if it's in res it's in texts[doc]
        index1 = res[0]
        if res[-1]+10 > len(texts[doc]):
            index2 = res[-1]
        elif res[-1]+10 < len(texts[doc]):
            index2 = res[-1]+10
    elif res[0]-10 > 0:
        index1 = res[0]-10
        if res[-1]+10 > len(texts[doc]):
            index2 = len(texts[doc])
        elif res[-1]+10 < len(texts[doc]):
            index2 = res[-1]+10

    # want to extend res. need to be sure what am adding to res is in texts[doc]

    resultContext = [num1 for num1 in range(index1,index2) if num1 in set(texts[doc].keys()) ] + \
                    [texts[doc][z] for z in res] + \
                    [num2 for num2 in range(index1,index2) if num2 in set(texts[doc].keys())]

    return resultContext

# def dict_to_html(dict):
#     final = ['<table><row>' + '<th>______</th>' + ''.join(['<th>'+label+'</th>'\
#        for label in labels[modifierType]+['fn', 'tp', 'precision', 'recall', 'f-score']]) + '</row>']
#     for key1 in dict:
#         final.append('<row>')
#         final.append('<th>' + str(key1) + '</th>')
#         for key2 in labels[modifierType]:
#             num = dict[key1][key2]
#             final.append('<td>'+str(num)+'</td>')
#         final.append('</row>')
#     final.append('</table>')
#     final = ''.join(final)
#     with open(os.path.join(path, 'confusionMatrix.html'), 'w') as out:
#         out.write('<html><head></head><body>')
#         out.write(final)
#         out.write('<br/><p/>')
#         out.write('<iframe width="800px" src="' + path + '\\' + 'cmContext.html"></iframe></body></html>')
#     out.close()

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

            if key in set(eng_li[i_mid].entries):
                return i_mid
            elif sorted(list(eng_li[i_mid].entries))[-1] > key:
                return binary_search(eng_li, gs_li, key, i_min, i_mid-1)
            elif sorted(list(eng_li[i_mid].entries))[0] < key:
                return binary_search(eng_li, gs_li, key, i_mid+1, i_max)


def find_pair(fname):
    return fname[:-3] + 'out.xml'


def process_entries(entries):
    # If you're having problems pulling these, check that MIM in the xml is either a scope or term annotation type
        mimChildren = [entry.firstChild for entry in entries\
                       if (entry.firstChild.localName == 'scope' or entry.firstChild.localName == 'term')]

        for child in mimChildren:
            entries = sorted(int(binding.getAttribute('ref').split('_')[1]) \
                             for binding in child.getElementsByTagNameNS('*', 'narrativeBinding'))
            label = [child.getAttribute('code') for child in child.getElementsByTagNameNS('*', 'code')\
                     if child.getAttribute('code') != '\\' and child.getAttribute('displayName') != "Lifelong"][0]
            #print "entries: ", entries
            if mode == "gs" and len(entries) > 0 and label in labels[modifierType]:
                if remapping is True:
                        #add all the rest of the remappings beyond Temporality here, in the future
                        if label == u'RECENTPAST':
                            gsMims[doc].append(Mim(entries, \
                                                   [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], u'PAST'))
                        elif label == u'FUTURE':
                            gsMims[doc].append(Mim(entries, \
                                                   [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], u'PRESENT'))
                        else:
                            gsMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
                else:
                    gsMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
            elif mode == 'eng' and len(entries) > 0 and label in labels[modifierType]:
                if remapping is True:
                    #add all the rest of the remappings beyond Temporality here, in the future
                    if label == u'RECENTPAST':
                        engMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], u'PAST'))
                    elif label == u'FUTURE':
                        engMims[doc].append(Mim(entries, \
                                                [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], u'PRESENT'))
                    else:
                        engMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
                else:
                    engMims[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
            del entries
            del label
        del mimChildren


def data_to_matrix(tp, fp, fn):

    # Add true positive and mismatch data to matrix
    for m in tp:
        matrix.loc[m.label, m.label] += 1

    for m in fp:
        matrix.loc[m.gsLabel, m.engLabel] += 1

    matrix['totals'] = matrix.sum(axis=1)

    for m in fn:
        matrix.loc[m.gsLabel, 'fn'] += 1

    matrix['tp'] = numpy.diag(matrix)

    matrix['precision'] = matrix.tp/matrix.totals
    matrix['recall'] = matrix.tp/(matrix.fn + matrix.tp)
    matrix['f-score'] = 2*((matrix.precision * matrix.recall)/(matrix.precision + matrix.recall))

    del matrix['tp']
    del matrix['totals']

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
    gsMims[doc] = sorted(gsMims[doc], key=attrgetter('entries'))


    mode = "eng"
    engMims[doc] = []
    process_entries(parse(os.path.join(path, find_pair(doc))).getElementsByTagName('entry'))
    engMims[doc] = sorted(engMims[doc], key=attrgetter('entries'))

    i = 0
    while i < len(gsMims[doc]):
        # print "running binary search for: ", gsMims[doc][i]
        match = binary_search(engMims[doc], gsMims[doc][i], gsMims[doc][i].entries[0], 0, len(engMims[doc])-1)

        if is_namedtuple_instance(match):
            if not doc in falseNeg:
                falseNeg[doc] = []
            contextRange = range(match.entries[0]-10,match.entries[0]) + \
                           match.entries+range(match.entries[-1],match.entries[-1]+10)
            temp = fnMim(doc, match.entries, match.tokens, match.label,\
                         [re.sub(r'\n', ' ', texts[doc][i]) for i in contextRange if i in set(texts[doc].keys())])
            falseNeg[doc].append(temp)
        elif type(match) == int:
            # print match
            # print "gsMims and engMims to be compared: ", gsMims[doc][i].tokens, engMims[doc][match].tokens
            if difflib.SequenceMatcher(None, gsMims[doc][i].tokens, engMims[doc][match].tokens).ratio() >= .5:
                if gsMims[doc][i].label == engMims[doc][match].label:
                    if doc not in truePos:
                        truePos[doc] = []
                    truePos[doc].append(engMims[doc][match])
                elif gsMims[doc][i].label != engMims[doc][match].label:
                    if doc not in mismatchFp:
                        mismatchFp[doc] = []
                    contextRange = range(engMims[doc][match].entries[0]-10, engMims[doc][match].entries[0]) +\
                                   engMims[doc][match].entries + \
                                   range(engMims[doc][match].entries[-1], engMims[doc][match].entries[-1]+10)
                    mismatchFp[doc].append(mismatchMim(
                                            doc,
                                            gsMims[doc][i].entries, engMims[doc][match].entries,
                                            gsMims[doc][i].tokens, engMims[doc][match].tokens,
                                            gsMims[doc][i].label, engMims[doc][match].label,
                                            [re.sub(r'\n', ' ', texts[doc][i]) for i in contextRange\
                                             if i in set(texts[doc].keys())]))

                                            #merge_sequences_get_context(gsMims[doc][i].contexts,
                                            # engMims[doc][match].contexts, doc)))
            else:
                # not catching everything here -- need mims not caught by binary search also
                if doc not in spontFp:
                    spontFp[doc] = []
                spontFp[doc].append(engMims[doc][match])
        i += 1

# print "True Positives"
# print [truePos[doc] for doc in truePos]
print "\n\n\n"
print "Mismatch FP"
print mismatchFp
print "\n\n\n"
# print "Spontaneous FP"
# print [doc + ": " + str(spontFp[doc]) for doc in spontFp]
# print "\n\n\n"
# print "False Negative"
# print [doc + ": " + str(falseNeg[doc]) for doc in falseNeg]

# Quick Testing

# if Mim(entries=set([545, 546, 547, 548, 549, 550, 551]), tokens=[u'history ', u'of ', u'any ', u'alcohol ', u'or ', u'drug ', u'abuse. '], label=u'PAST') in truePos['ClinicalDocument_2202830448.xml']:
#     print "1 -True"
# if Mim(entries=set([662, 663, 664, 665, 666, 667]), tokens=[u'The ', u"patient's ", u'parents ', u'have ', u'passed ', u'away '], label=u'PAST') in falseNeg['ClinicalDocument_2202830448.xml']:
#     print "2 -True"
# if Mim(entries=set([1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416]), tokens=[u'last ', u'2D ', u'echocardiogram ', u'to ', u'look ', u'for ', u'any ', u'other ', u'explanation ', u'for ', u'his ', u'atrial ', u'fibrillation. '], label=u'PAST') in spontFp['ClinicalDocument_2202830448.xml']:
#     print "3 -True"
#Mim(entries=[], tokens=[], label='') in mismatchFp['ClinicalDocument_2202830448.xml']

[tpFlat.extend(truePos[doc]) for doc in truePos]
[fnFlat.extend(falseNeg[doc]) for doc in falseNeg]
[mismatchFlat.extend(mismatchFp[doc]) for doc in mismatchFp]

labelCombos = [label1+label2 for label1 in labels[modifierType] for label2 in labels[modifierType]]

for mismatch in mismatchFlat:
    if not mismatch.gsLabel+mismatch.engLabel in confusions:
        confusions[mismatch.gsLabel+mismatch.engLabel] = []
    confusions[mismatch.gsLabel+mismatch.engLabel].append(mismatch)

data_to_matrix(tpFlat, mismatchFlat, fnFlat)

matrix = matrix.replace([numpy.inf, -numpy.inf], numpy.nan)
matrix = matrix.fillna(0)

##
## Contexts
##

contextOut = ['<html><head></head><body><table>']
if any(mismatchFlat):
    for mim in mismatchFlat:
        k = 0
        contextOut.append('<tr>')
        #for each mim per doc
        contextOut.append('<th>' + mim.doc + '</th>')
        contextOut.append('<th>' + mim.gsLabel + " confused as " + mim.engLabel + '</th>')
        goldMatch = difflib.SequenceMatcher(None, mim.context, mim.gsTokens).get_matching_blocks()[0]
        engMatch = difflib.SequenceMatcher(None, mim.context, mim.engTokens).get_matching_blocks()[0]
        #engGoldMatch = difflib.SequenceMatcher(None,
        # mismatchFp[doc][k].gsTokens, mismatchFp[doc][k].engTokens).get_matching_blocks()[0]
        justEng = set(mim.engEntries) - set(mim.gsEntries)
        justGs = set(mim.gsEntries) - set(mim.engEntries)
        intrscEngGs = set(mim.gsEntries) & set(mim.engEntries)

        if justGs and justEng:
            if mim.gsEntries[0] < mim.engEntries[0]:
                #gold happens first
                colorCodedContext = ''.join(mim.context[0:goldMatch[0]]) + \
                                    '<font style="background-color:blue;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justGs))]) + \
                                    '</strong></font><font style="background-color:purple;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(intrscEngGs))]) + \
                                    '</strong></font><font style="background-color:red;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justEng))]) + \
                                    '</strong></font>' + \
                                    ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

            elif mim.gsEntries[0] > mim.engEntries[0]:
                colorCodedContext = ''.join(mim.context[0:engMatch[0]]) + \
                                    '<font style="background-color:red;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justEng))]) +\
                                    '</strong></font><font style="background-color:purple;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(intrscEngGs))]) + \
                                    '</strong></font><font style="background-color:blue;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justGs))]) + \
                                    '</strong></font>' + \
                                    ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

        if justGs and not justEng:
            if mim.gsEntries[0] < mim.engEntries[0]:
                colorCodedContext = ''.join(mim.context[0:goldMatch[0]]) + \
                                    '<font style="background-color:blue;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justGs))]) + \
                                    '</strong></font><font style="background-color:purple;color:white;"><strong>' +\
                                    ''.join([texts[mim.doc][i] for i in sorted(list(intrscEngGs))]) + \
                                    '</strong></font>' + \
                                    ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

            elif mim.gsEntries[0] > mim.engEntries[0]:
                colorCodedContext = ''.join(mim.context[0:engMatch[0]]) + \
                                    '<font style="background-color:purple;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(intrscEngGs))]) + \
                                    '</strong></font><font style="background-color:blue;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justGs))]) + \
                                    '</strong></font>' + \
                                    ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

        elif justEng and not justGs:
            if mim.gsEntries[0] < mim.engEntries[0]:
                colorCodedContext = ''.join(mim.context[0:goldMatch[0]]) + \
                                    '<font style="background-color:purple;color:white;"><strong>' + \
                                    ''.join([texts[mim.oc][i] for i in sorted(list(intrscEngGs))]) + \
                                    '</strong></font><font style="background-color:red;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justEng))]) + \
                                    '</strong></font>' + \
                                    ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

            elif mim.gsEntries[0] > mim.engEntries[0]:
                colorCodedContext = ''.join(mim.context[0:engMatch[0]]) + \
                                    '<font style="background-color:red;color:white;"><strong>' + \
                                    ''.join([texts[mim.doc][i] for i in sorted(list(justEng))]) + \
                                    '</strong></font><font style="background-color:purple;color:white;"><strong>' +\
                                    ''.join([texts[mim.doc][i] for i in sorted(list(intrscEngGs))]) + \
                                    '</strong></font>' + \
                                    ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

        elif not justEng and not justGs:
            colorCodedContext = ''.join(mim.context[0:goldMatch[0]]) + \
                                '<font style="background-color:purple;color:white;"><strong>' + \
                                ''.join([texts[mim.doc][i] for i in sorted(list(intrscEngGs))]) + \
                                '</strong></font>' + \
                                ''.join(mim.context[goldMatch[0]+goldMatch[2]+1:])

        # colorCodedOutContext = mismatchFp[doc][k].gsTokens[0:begIx] + \
        #                     ['<font style="background-color:blue;color:white;">'] + \
        #                     mismatchFp[doc][k].gsTokens[begIx:begIx+engGoldMatch[2]] + ['</font>'] + \
        #                     mismatchFp[doc][k].gsTokens[begIx+engGoldMatch[2]+1:]

        contextOut.append('<td>' + ''.join(colorCodedContext) + '</td>')
        #contextOut.append('<td>' + ''.join(colorCodedGsContext) + '</td>')
        #contextOut.append('<td>' + ''.join(colorCodedEngContext) + '</td>')
        #contextOut.append('<td>' + ''.join(colorCodedOutContext) + '</td>')
        contextOut.append('</tr>')
    contextOut.append('</table></body></html>')
else:
    contextOut.append('<td> NO MISMATCHES FOUND! </td></tr></table></body></html>')

contextOut = ''.join(contextOut)

fnFlat = sorted(fnFlat, key=attrgetter('gsLabel'))
print "fnFlat RIGHT HERE: ", fnFlat

fnContext = ['<html><head></head><body><table>']
if any(fnFlat):
    print "******fnFlat[0] : ", fnFlat[0]
    currLabel = fnFlat[0].gsLabel
    i = 0
    while i < len(fnFlat):
        print "fnFlat[i].gsLabel : ", fnFlat[i].gsLabel, " and ", currLabel
        if fnFlat[i].gsLabel != currLabel:
            currLabel = fnFlat[i].gsLabel
            fnContext.append('<tr><h1>' + currLabel + '</h1></tr>')
        fnContext.append('<tr>')
        fnContext.append('<th>' + fnFlat[i].doc + '</th>')
        fnContext.append('<th>' + fnFlat[i].gsLabel + " wasn't caught </th>")
        goldMatch = difflib.SequenceMatcher(None, fnFlat[i].context,\
                                            fnFlat[i].tokens).get_matching_blocks()[0]
        fnColorCoded = ''.join(fnFlat[i].context[0:goldMatch[0]]) + \
             '<font style="background-color:yellow"><strong>' + \
             ''.join(fnFlat[i].tokens) + "</strong></font>" + \
             ''.join(fnFlat[i].context[goldMatch[0]+goldMatch[2]+1:])
        fnContext.append('<td>' + ''.join(fnColorCoded) + '</td>')
        fnContext.append('</tr>')
        i += 1
    fnContext.append('</table></body></html>')
else:
    fnContext.append('<td> NO FALSE NEGATIVES FOUND! </td></tr></table></body></html>')

fnContext = ''.join(fnContext)


##
## HTML Output
##

dictMatrix = matrix.to_dict(orient="series")

print "dictMatrix: ", dictMatrix

#dict_to_html(dictMatrix)

#'<a href="' + 'confusionMatrix_' + modifierType + ".html#" + label1 + "x" + label2 + '">' + str(val) + '</a>'

# for column in labels[modifierType]:
#   while i <
#     matrix[column] = matrix[column].apply(lambda x: '<a href="confusionMatrix_' + modifierType + ".html#" + label1 +
#        "x" + label2 + '">' + str(val) + '</a>)
HTML(matrix.to_html(escape=False, index=True, classes='table', buf=os.path.join(path, 'confusionMatrix.html')))

root = ET.parse(os.path.join(path, 'confusionMatrix.html')).getroot()

# print "here it comes: "
# for cell in root.findall('.//row'):
#     print ET.tostring(cell)
# for thing in ET.tostringlist(root):
#     print thing

html = '<html style="text-align:center;"><head></head><body>' +\
               '<div style="display:inline-block;margin: 0px auto;">' + ET.tostring(root) + '</div>' +\
               '<br/><p/><div style="width:49%;height:80%;float:left;"><iframe seamless="seamless" scrolling="yes" frameborder="0" src="' +\
                os.path.join(path, 'cmContext.html') +\
                '" style="overflow:hidden;height:100%;width:100%" height="100%" width="100%"></iframe></div>' +\
                '<div style="width:49%;height:80%;float:left;"><iframe seamless="seamless" scrolling="yes"\
                 frameborder="0" src="' + os.path.join(path, 'fnContext.html') + \
                '" style="overflow:hidden;height:100%;width:100%" height="100%" width="100%"></iframe></div></body></html>'

print "html: ", html

with open(os.path.join(path, 'confusionMatrix.html'), 'w') as out:
    out.write(html)
out.close()

with open(os.path.join(path, 'cmContext.html'), 'w') as outFrame:
    outFrame.write(contextOut)
outFrame.close()

with open(os.path.join(path, 'fnContext.html'), 'w') as outFn:
    outFn.write(fnContext)
outFn.close()

print "\n\nTook ", datetime.datetime.now()-startTime, " to run ", len(goldDocs), " files."