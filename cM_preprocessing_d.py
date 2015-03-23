import numpy
import pandas
from xml.dom.minidom import parse
import os, datetime, sys, re
from operator import attrgetter
from collections import namedtuple
import difflib

######################################################################################################################
##
## CONFUSY Confusion Matrixer v2
##
## - Tested on Python 2.7.6
## - Document tokenization with gaps now handled
## - Much quicker on huge sets (tested up to 1048 gold + 1048 eng docs)
## - Mim overlap is hinged on a phrase similarity ratio, adjustable on line 255
## - Tested on Temporality, the i2b2 corpus, ... will work with any engine, you just need to be sure to catch the respective mim type (i.e. edit line 3 of process_entries())
##
## To run: python confusy.py <filepath> <engine>
##
## "Remapping?"
## - say "True" to map non-engine gold labels to the closest engine counterparts, otherwise say "False"
##
## Faults of this script / ways it can be improved:
## - narrativeBinding @ref nodes in CDA aren't often in sorted order. The below should obviously be 's/p Endovascular Aortic Aneurysm Repair'
##  e.g. Mim(entries=[4, 5, 6, 7, 8, 401, 402], tokens=[u's ', u'Endovascular ', u'Aortic ', u'Aneurysm ', u'Repair.  ', u'/ ', u'p '], label=u'PAST')
##  This should be easily fixed with tokenizeOldXslt.py though, which takes weirdo tokenization and, preserving MIM bindings, reassigns @ref / @IDs in order


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


def process_entries(mimDict, doc, entries, remapping, texts, typeLabels):

    Mim = namedtuple("Mim", "entries, tokens, label")

    # If you're having problems pulling these, check that MIM in the xml is either a scope or term annotation type
    mimChildren = [entry.firstChild for entry in entries\
                   if (entry.firstChild.localName == 'scope' or entry.firstChild.localName == 'term')]

    for child in mimChildren:
        entries = sorted(int(binding.getAttribute('ref').split('_')[1]) for binding in child.getElementsByTagNameNS('*', 'narrativeBinding'))
        if not entries: # section bindings would also be caught up to this point -- skipping those of course
            continue
        label = [child.getAttribute('code') for child in child.getElementsByTagNameNS('*', 'code')\
                 if child.getAttribute('code') != '\\' and child.getAttribute('displayName') != "Lifelong"][0]
        #print "entries: ", entries
        if label in typeLabels:
            if remapping is True:
                    #add all the rest of the remappings beyond Temporality here, in the future
                    if label == u'RECENTPAST':
                        mimDict[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], u'PAST'))
                    elif label == u'FUTURE':
                        mimDict[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], u'PRESENT'))
                    else:
                        mimDict[doc].append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
            else:
                mimDict.append(Mim(entries, [re.sub(r'\n', ' ', texts[doc][i]) for i in entries], label))
        del entries
        del label
    del mimChildren


def data_to_matrix(matrix, tp, fp, fn):

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

def dict_to_html(matrixDict):

    #Looks like {'index': [u'PAST', u'RECENTPAST', u'FUTURE', u'PRESENT', u'UNDEFINED'], 'data': [[157.0, 0.0, 0.0, 0.0, 0.0, 108.0, 1.0, 0.5924528301886792, 0.7440758293838862], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, inf, inf, nan], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, inf, inf, nan], [4.0, 0.0, 0.0, 40.0, 0.0, 82.0, 0.9090909090909091, 0.32786885245901637, 0.4819277108433735], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, inf, inf, nan]], 'columns': [u'PAST', u'RECENTPAST', u'FUTURE', u'PRESENT', u'UNDEFINED', 'fn', 'precision', 'recall', 'f-score']}
    final = ['<div class="table-responsive"><table class="table table-striped"><thead><tr><th></th>' + ''.join('<th>' + column + '</th>' for column in matrixDict['columns']) + '</tr></thead><tbody>']

    y = 0
    while y < len(matrixDict['index']):
        final.append('<tr>')
        print "y : ", y
        final.append('<th>' + matrixDict['columns'][y] + '</th>')
        z = 0
        while z < len(matrixDict['columns']):
            print "z : ", z
            print "data point: ", matrixDict['data'][y][z]
            # first five cols of the matrix table
            if z <= 4:
                value = '<a href="fpContext.html#' + matrixDict['index'][y] + "x" + matrixDict['columns'][z] + '" target="fp">' + str(int(matrixDict['data'][y][z])) + "</a>"
            # sixth col is fn
            elif z == 5:
                value = '<a href="fnContext.html#' + matrixDict['index'][y] + 'xfn" target="fn">' + str(int(matrixDict['data'][y][z])) + "</a>"
            # no links for the rest
            else:
                value = str(matrixDict['data'][y][z])
            final.append('<td>' + value + '</td>')
            z += 1
        final.append('</tr>')
        y += 1
    final.append('</tbody></table></div>')
    final = ''.join(final)

    return final


def main():

    startTime = datetime.datetime.now()
    print startTime

    ##
    ## Variables
    ##

    # path = sys.argv[1]
    path = "C:\\Users\\courtney.zelinsky\\Desktop\\temporalityTestingSub"
    # path = "C:\\Users\\courtney.zelinsky\\Desktop\\chapmanCorpus"

    #modifierType = sys.argv[2]
    modifierType = 'T'
    # modifierType = 'i2b2'

    # print "Remapping? Enter True or False"
    # remapping = raw_input()
    remapping = True

    if not os.path.exists(path):
        raise Exception('Invalid path(s)')


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

    texts = {}

    mismatchMim = namedtuple("mismatchMim", "doc, gsEntries, engEntries, gsTokens, engTokens, gsLabel, engLabel, context")
    fnMim = namedtuple("fnMim", "doc, entries, tokens, gsLabel, context")

    labels = {
            "S":[u'SUBJECT', u'PROVIDER', u'AUTHOR', u'BABY', u'NONFAMILY', u'FAMILY', u'SIBLING', u'MOTHER', u'FATHER',
                 u'AUNT', u'UNCLE', u'GRANDPARENT', u'CHILD'],
            "C": [u'MAYBE', u'CERTAIN', u'HEDGED', u'HYPOTHETICAL', u'RULED_OUT', u'NEGATED'],
            "D": [u'LAST_NAME', u'MALE_NAME', u'FEMALE_NAME', u'PHONE_NUMBER', u'MEDICAL_RECORD_NUMBER',
                  u'ABSOLUTE_DATE', u'DATE', u'ADDRESS', u'LOCATION', u'AGE', u'SOCIAL_SECURITY_NUMBER',
              u'CERTIFICATE_OR_LICENSE_NUMBER', u'ID_OR_CODE_NUMBER', u'NAME', u'ORGANIZATION', u'URL',
                  u'E_MAIL_ADDRESS',u'TIME', u'OTHER', u'HOSPITAL', u'INITIAL', u'HOSPITAL_SUB'],
            "T": [u'PAST', u'RECENTPAST', u'FUTURE', u'PRESENT', u'UNDEFINED'],
            "i2b2":[u'NEGATIVE'],
            }

    matrix = pandas.DataFrame(index=labels[modifierType],
                              columns=labels[modifierType]+['totals', 'fn', 'tp', 'precision', 'recall', 'f-score'])
    matrix = matrix.fillna(0)
    pandas.set_option('display.max_columns', 1000)

    ##
    ## Get & Classify Mims
    ##

    for doc in goldDocs:
        texts[doc] = {}
        goldParsed = parse(os.path.join(path, doc))
        for contentNode in goldParsed.getElementsByTagNameNS('*', 'content'):
            getTokenization = int(contentNode.getAttribute('ID').split('_')[1])
            texts[doc][getTokenization] = contentNode.firstChild.nodeValue

        gsMims[doc] = []
        process_entries(gsMims, doc, goldParsed.getElementsByTagName('entry'), remapping, texts, labels[modifierType])
        gsMims[doc] = sorted(gsMims[doc], key=attrgetter('entries'))


        engMims[doc] = []
        process_entries(engMims, doc, parse(os.path.join(path, find_pair(doc))).getElementsByTagName('entry'),
                        remapping, texts, labels[modifierType])
        engMims[doc] = sorted(engMims[doc], key=attrgetter('entries'))

        i = 0
        while i < len(gsMims[doc]):

            match = binary_search(engMims[doc], gsMims[doc][i], gsMims[doc][i].entries[0], 0, len(engMims[doc])-1)

            if is_namedtuple_instance(match):
                if not doc in falseNeg:
                    falseNeg[doc] = []
                contextRange = range(match.entries[0]-10,match.entries[0]) + \
                               match.entries+range(match.entries[-1],match.entries[-1]+10)
                temp = fnMim(doc, match.entries, match.tokens, match.label,
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

    [tpFlat.extend(truePos[doc]) for doc in truePos]
    [fnFlat.extend(falseNeg[doc]) for doc in falseNeg]
    [mismatchFlat.extend(mismatchFp[doc]) for doc in mismatchFp]

    # labelCombos = [label1+label2 for label1 in labels[modifierType] for label2 in labels[modifierType]]
    #
    # for mismatch in mismatchFlat:
    #     if not mismatch.gsLabel+mismatch.engLabel in confusions:
    #         confusions[mismatch.gsLabel+mismatch.engLabel] = []
    #     confusions[mismatch.gsLabel+mismatch.engLabel].append(mismatch)

    matrix = matrix.replace([numpy.inf, -numpy.inf], numpy.nan)
    matrix = matrix.fillna(0)

    data_to_matrix(matrix, tpFlat, mismatchFlat, fnFlat)
    matrixDict = matrix.to_dict(orient="split")

    ##
    ## Concordancing & Overlaps
    ##

    mismatchFlat = sorted(mismatchFlat, key=attrgetter("gsLabel", "engLabel"))

    fpContext = ['<html><link href="http://fonts.googleapis.com/css?family=Lato:300" rel="stylesheet" type="text/css"><head></head><body style="font-family:\'Lato\', sans-serif;"><table>']
    if any(mismatchFlat):
        j = 0
        fpContext.append('<tr id="' + mismatchFlat[0].gsLabel + "x" + mismatchFlat[0].engLabel + '"><th colspan="3"><font size="18px">' + mismatchFlat[0].gsLabel + " confused as " + mismatchFlat[0].engLabel + '</font></th></tr>')
        while j < len(mismatchFlat):
            if mismatchFlat[j].gsLabel != mismatchFlat[j-1].gsLabel and j > 1:
                currLabel1 = mismatchFlat[j].gsLabel
                if mismatchFlat[j].engLabel != mismatchFlat[j-1].engLabel and j > 1:
                    currLabel2 = mismatchFlat[j].engLabel
                fpContext.append('<tr id="' + currLabel1 + "x" + currLabel2 + '"><th colspan="3"><font size="18px">' + currLabel1 + " confused as " + currLabel2 + '</font></th></tr>')
            elif mismatchFlat[j].engLabel != mismatchFlat[j-1].engLabel and j > 1:
                currLabel2 = mismatchFlat[j].engLabel
                currLabel1 = mismatchFlat[j].gsLabel
                fpContext.append('<tr id="' + currLabel1 + "x" + currLabel2 + '"><th colspan="3"><font size="18px">' + currLabel1 + " confused as " + currLabel2 + '</font></th></tr>')

            fpContext.append('<tr>')
            fpContext.append('<th>' + mismatchFlat[j].doc + '</th>')
            #fpContext.append('<th>' + mismatchFlat[j].gsLabel + " confused as " + mismatchFlat[j].engLabel + '</th>')

            goldMatch = difflib.SequenceMatcher(None, mismatchFlat[j].context, mismatchFlat[j].gsTokens).get_matching_blocks()[0]
            engMatch = difflib.SequenceMatcher(None, mismatchFlat[j].context, mismatchFlat[j].engTokens).get_matching_blocks()[0]

            justEng = set(mismatchFlat[j].engEntries) - set(mismatchFlat[j].gsEntries)
            justGs = set(mismatchFlat[j].gsEntries) - set(mismatchFlat[j].engEntries)
            intrscEngGs = set(mismatchFlat[j].gsEntries) & set(mismatchFlat[j].engEntries)

            if justGs and justEng:
                if mismatchFlat[j].gsEntries[0] < mismatchFlat[j].engEntries[0]:
                    # ...then gold annotation happens first
                    colorCodedContext = ''.join(mismatchFlat[j].context[0:goldMatch[0]]) + \
                                        '<font style="background-color:blue;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justGs))]) + \
                                        '</strong></font><font style="background-color:purple;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                        '</strong></font><font style="background-color:red;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justEng))]) + \
                                        '</strong></font>' + \
                                        ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

                elif mismatchFlat[j].gsEntries[0] > mismatchFlat[j].engEntries[0]:
                    # ...then eng annotation happens first
                    colorCodedContext = ''.join(mismatchFlat[j].context[0:engMatch[0]]) + \
                                        '<font style="background-color:red;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justEng))]) +\
                                        '</strong></font><font style="background-color:purple;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                        '</strong></font><font style="background-color:blue;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justGs))]) + \
                                        '</strong></font>' + \
                                        ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

            if justGs and not justEng:
                if mismatchFlat[j].gsEntries[0] < mismatchFlat[j].engEntries[0]:
                    colorCodedContext = ''.join(mismatchFlat[j].context[0:goldMatch[0]]) + \
                                        '<font style="background-color:blue;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justGs))]) + \
                                        '</strong></font><font style="background-color:purple;color:white;"><strong>' +\
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                        '</strong></font>' + \
                                        ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

                elif mismatchFlat[j].gsEntries[0] > mismatchFlat[j].engEntries[0]:
                    colorCodedContext = ''.join(mismatchFlat[j].context[0:engMatch[0]]) + \
                                        '<font style="background-color:purple;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                        '</strong></font><font style="background-color:blue;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justGs))]) + \
                                        '</strong></font>' + \
                                        ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

            elif justEng and not justGs:
                if mismatchFlat[j].gsEntries[0] < mismatchFlat[j].engEntries[0]:
                    colorCodedContext = ''.join(mismatchFlat[j].context[0:goldMatch[0]]) + \
                                        '<font style="background-color:purple;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                        '</strong></font><font style="background-color:red;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justEng))]) + \
                                        '</strong></font>' + \
                                        ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

                elif mismatchFlat[j].gsEntries[0] > mismatchFlat[j].engEntries[0]:
                    colorCodedContext = ''.join(mismatchFlat[j].context[0:engMatch[0]]) + \
                                        '<font style="background-color:red;color:white;"><strong>' + \
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(justEng))]) + \
                                        '</strong></font><font style="background-color:purple;color:white;"><strong>' +\
                                        ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                        '</strong></font>' + \
                                        ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

            elif not justEng and not justGs:
                colorCodedContext = ''.join(mismatchFlat[j].context[0:goldMatch[0]]) + \
                                    '<font style="background-color:purple;color:white;"><strong>' + \
                                    ''.join([texts[mismatchFlat[j].doc][n] for n in sorted(list(intrscEngGs))]) + \
                                    '</strong></font>' + \
                                    ''.join(mismatchFlat[j].context[goldMatch[0]+goldMatch[2]+1:])

            fpContext.append('<td>' + ''.join(colorCodedContext) + '</td>')
            fpContext.append('</tr>')
            j += 1
        fpContext.append('</table></body></html>')
    else:
        fpContext.append('<td> NO MISMATCHES FOUND! </td></tr></table></body></html>')

    fpContext = ''.join(fpContext)

    fnFlat = sorted(fnFlat, key=attrgetter('gsLabel'))
    print "fnFlat RIGHT HERE: ", fnFlat

    fnContext = ['<html><link href="http://fonts.googleapis.com/css?family=Lato:300" rel="stylesheet" type="text/css"><head></head><body style="font-family:\'Lato\', sans-serif;"><table>']
    if any(fnFlat):
        fnContext.append('<tr id="' + fnFlat[0].gsLabel + 'xfn"><th colspan="3"><font size="18px">' + fnFlat[0].gsLabel + '</font></th></tr>')
        i = 0
        while i < len(fnFlat):
            #print "fnFlat[i].gsLabel : ", fnFlat[i].gsLabel, " and ", fnFlat[i-1].gsLabel
            if fnFlat[i].gsLabel != fnFlat[i-1].gsLabel and i > 1:
                currLabel = fnFlat[i].gsLabel
                fnContext.append('<tr id="' + currLabel + 'xfn"><th colspan="3"><font size="18px">' + currLabel + '</font></th></tr>')
            fnContext.append('<tr>')
            fnContext.append('<th>' + fnFlat[i].doc + '</th>')
            goldMatch = difflib.SequenceMatcher(None, fnFlat[i].context, fnFlat[i].tokens).get_matching_blocks()[0]
            fnColorCoded = ''.join(fnFlat[i].context[0:goldMatch[0]]) + \
                 '<font style="background-color:yellow;"><strong>' + \
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
    ## Report Output
    ##

    dict_to_html(matrix.to_dict(orient="split"))

    if remapping is True:
        remappingNote = '<p><strong> Stats were calculated with remapping ON -- any labels in the gold set not in the engine set have been set to their closest engine counterpart. </strong></p>'
    else:
        remappingNote = '<p><strong> Stats were calculated with remapping OFF - all gold and engine labels have been counted as is'

    html =  '<html style="text-align:center;">' +\
            "<link href='http://fonts.googleapis.com/css?family=Lobster' rel='stylesheet' type='text/css'>" +\
            '<link href="http://fonts.googleapis.com/css?family=Lato:300" rel="stylesheet" type="text/css">' +\
            '<head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width, initial-scale=1">' +\
            '<link href="http://getbootstrap.com/dist/css/bootstrap.min.css" rel="stylesheet"></head><body style="font-family:\'Lato\',sans-serif;">' +\
            """    <nav class="navbar navbar-inverse navbar-fixed-top">
              <div class="container-fluid">
                <div class="navbar-header">
                  <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                  </button>
                  <a class="navbar-brand" href="confusionMatrix.html"><span style="font-family: 'Lobster', cursive;">Confusy.py :</span> A fancy little data visualization script</a>
                </div>
                <div id="navbar" class="navbar-collapse collapse">
                  <ul class="nav navbar-nav navbar-right">
                    <li><a href="#">Summary</a></li>
                    <li><a href="#">Matrix</a></li>
                    <li><a href="#">Mismatches</a></li>
                    <li><a href="#">Help</a></li>
                    <li><a href="#">About</a></li>
                  </ul>
                </div>
              </div>
            </nav>""" +\
            '<div style="display:inline-block;margin: 0px auto;margin-top: 100px;">' + dict_to_html(matrixDict) + '</div>' +\
            '<br/>' + remappingNote + '<p/>' + \
            '<p><a href="fnContext.html#PRESENTxfn" target="fn"> Also let\'s see if this scrolls </a>' +\
            '<div style="width:49%;height:80%;float:left;"><iframe name="fp" id="fp" seamless="seamless" scrolling="yes" frameborder="0" src="' +\
            os.path.join(path, 'fpContext.html') +\
            '" style="overflow:hidden;height:100%;width:100%" height="100%" width="100%"></iframe></div>' +\
            '<div style="width:49%;height:80%;float:left;"><iframe name="fn" id="fn" seamless="seamless" \
            scrolling="yes" frameborder="0" src="' + os.path.join(path, 'fnContext.html') + \
            '" style="overflow:hidden;height:100%;width:100%" height="100%" width="100%"></iframe></div>' +\
            '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script><script src="../../dist/js/bootstrap.min.js"></script>' +\
            "<script>$('a').click(function(){$('html, iframe').animate({scrollTop: $( $(this).attr('href') ).offset().top}, 500);return false;});</script></body></html>"

    print "html: ", html

    with open(os.path.join(path, 'confusionMatrix.html'), 'w') as out:
        out.write(html)
    out.close()

    with open(os.path.join(path, 'fpContext.html'), 'w') as outFrame:
        outFrame.write(fpContext)
    outFrame.close()

    with open(os.path.join(path, 'fnContext.html'), 'w') as outFn:
        outFn.write(fnContext)
    outFn.close()

    print matrix

    print "\n\nTook ", datetime.datetime.now()-startTime, " to run ", len(goldDocs), " files."

if __name__ in '__main__':
    main()