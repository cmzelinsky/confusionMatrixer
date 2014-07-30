# -*- coding: utf-8 -*-
# author : Courtney Zelinsky
# created : 5/13/14

#Purpose: Create confusion matrix for deid MIMs
#Data structure is a double dictionary: {filename : {entries : code}}
#Also generates reports on each individual confusion


import datetime, operator, os, pickle, sys, libxml2, xml.dom.minidom as minidom
import xml.etree.ElementTree
import xml.etree.ElementTree as ET
startTime = datetime.datetime.now()
path = 'C:/Users/courtney.zelinsky/Desktop/test'
if not os.path.exists(path):
    raise Exception('Invalid path')

xmls = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml' , os.listdir(path))
if not len(xmls) > 0:
    raise Exception('No .xml files in this directory')

def findPair(fname): 
    return fname[:-3] + 'out.xml'
			
def getResults(li):
    return sorted(li.iteritems(), key=operator.itemgetter(1), reverse = True)

def Round(Float):
    return "{0:.4f}".format(Float)

def getTotal(attr):
    return sum([int(v.firstChild.nodeValue) for v in doc.getElementsByTagName('Engine') if v.getAttribute('count') == attr])

##def listCompare(l1, l2):
##    return filter(lambda x: x not in list(l1), list(l2))

def getText(fname, entries):
    entries = entries.split(', ')
    doc = minidom.parse(path + '\\' + fname)
    docTemp = ET.parse(path + '\\' + fname)
    concept = []
    para = []
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
    para = '<span onclick="showHide(this)" style="cursor:pointer">Context <span class="plusMinus">[+]</span></span><br><span style="display:none">' + ''.join(para) + '</span>'
    return fname + separator + concept + separator + para

def errorAnalysis(gs, eng):
    allmims = pickle.load(open(os.path.join(path, 'allmims.txt')))
    flen = str(len(allmims)/2)
    errors = []
    for file in allmims:
        if not '.out' in file:
            for entry in allmims[file]:
                if entry in allmims[findPair(file)] and allmims[file][entry] == gs and allmims[findPair(file)][entry] == eng:
                    errors.append(getText(file, entry))
    if errors:
        with open(os.path.join(path, gs + ' x ' + eng + '.html'), 'w') as out:
            sys.stdout.write('(' + os.path.basename(out.name) + ')')
            out.write('<html>\n')
            out.write('<head>\n')
            out.write('<script language="javascript" type="text/javascript">\n')
            out.write("""function showHide(sender)
                {
                parent = sender.parentNode;
                PM = parent.getElementsByTagName('span')[1]
                ul = parent.getElementsByTagName('span')[2]
                if (ul.style.display != 'none')
                {
                    ul.style.display = 'none';
                    PM.innerHTML = '[+]';
                }
                else
                {
                    ul.style.display = 'block';
                    PM.innerHTML = '[-]';
                }
                }\n""")
            out.write('</script>\n')
            out.write('<title>' + 'Confusions between ' + gs + ' and ' + eng + '</title>\n')
            out.write('</head>\n')
            out.write('<body>\n')
            out.write('<h3>Confusions between ' + gs + ' and ' + eng + '</h3>\n')
            out.write('<h4>Found ' + str(len(errors)) + ' errors in ' + str(len(set([error.split('::::')[0] for error in errors]))) + ' documents</h4>\n')
            out.write('<h5>Generated at ' + str(datetime.datetime.now()).split('.')[0].split()[1] + ' on ' + str(datetime.datetime.now()).split('.')[0].split()[0] + '</h5>\n')
            out.write('<table border="1">\n\t<th>Document</th>\n\t<th>Concept</th>\n\t<th width="100%">Paragraph</th>\n')
            for para in errors:
                out.write('\t<tr>\n\t\t<td>' + para.replace('::::', '</td>\n\t\t\t<td>') + '</td>\n\t</tr>\n')
            out.write('</table>\n')
            out.write('</body>\n')
            out.write('</html>')
tp = {}
errors = {}
allmims = {}
f = 0
numFiles = len(xmls)
for file in xmls:
    f += 1
    if not file.endswith('.out.xml'):
        sys.stdout.write('Building MIM index for ' + file + '     (file ' + str(f) + ' of ' + str(numFiles) + ')...')
    else:
        sys.stdout.write('Building MIM index for ' + file + ' (file ' + str(f) + ' of ' + str(numFiles) + ')...')
    mimdict = {}
    document = minidom.parse(os.path.join(path, file))
    entries = document.getElementsByTagName('entry')
    for entry in entries:
        bindings = []
        for child in entry.firstChild.childNodes:
            if child.localName == 'binding':
                bindings.extend([narrativeBindings.getAttribute('ref') for narrativeBindings in child.childNodes])
##                print bindings
                Entries = ', '.join([str(binding) for binding in bindings])
                Value = str([child.getAttribute('code') for child in entry.firstChild.childNodes if child.localName == 'code']) # added if filter here, because why would we need the manual validation codes? 
                mimdict[Entries] = Value
    allmims[file] = mimdict
    print "allmims:"
    print allmims
    sys.stdout.write(' Done!\n\n\n')


for File in allmims:
    print "\nPrinting allmims[File] for File\n"
    print allmims[File]
    if not File.endswith('.out.xml'):
        pair = findPair(File)
##        if not allmims[File] == allmims[pair]: a check to make sure that the mim dics aren't the same
        for MIM in allmims[File]:
            print "Printing MIM"
            print MIM
            if MIM in allmims[pair]:
                print "->", allmims[File][MIM], allmims[pair][MIM]
                if allmims[File][MIM] == allmims[pair][MIM]:
                    if allmims[File][MIM] in tp:
                        tp[allmims[File][MIM]] += 1
                    else:
                        tp[allmims[File][MIM]] = 1
                else:
                    confusion = tuple([allmims[File][MIM], allmims[pair][MIM]]) # [0] = GS; [1] = ENG
                    if confusion in errors:
                        errors[confusion] += 1
                    else:
                        errors[confusion] = 1
print '\n\nTotal MIMs:', sum([tp[i] for i in tp]) + sum([errors[i] for i in errors])
print 'True Positives:', sum([tp[i] for i in tp])
print 'Errors:', sum([errors[i] for i in errors])
print '\n\nTRUE POSITIVES:\n\n'
for i in getResults(tp):
    print i[0], 'correctly identified as such', i[1], 'times'
print '\n\nERRORS:\n\n'
for i in getResults(errors):
    if  i[1] == 1:
        print i[0][0], 'mistakenly marked as', i[0][1], i[1], 'time'
    else:
        print i[0][0], 'mistakenly marked as', i[0][1], i[1], 'times'
savedErrors = errors
data = dict(errors)
for i in tp:
    data[(i, i)] = tp[i]

print '\n\nPerforming error analysis...\n'
currentdi = {}
vals = {'LAST_NAME', 'MALE_NAME', 'FEMALE_NAME', 'PHONE_NUMBER', 'MEDICAL_RECORD_NUMBER', 'ABSOLUTE_DATE', 'DATE', 'ADDRESS',
        'LOCATION', 'AGE', 'SOCIAL_SECURITY_NUMBER', 'CERTIFICATE_OR_LICENSE_NUMBER', 'ID_OR_CODE_NUMBER', 'NAME', 'ORGANIZATION',
        'URL', 'E_MAIL_ADDRESS', 'HOSPITAL', 'TIME', 'OTHER'}
with open(os.path.join(path, 'confusionMatrix.html'), 'w') as out:
    out.write('<html><head><title>Confusion Matrix</title></head><body>')
    out.write('<h4>Generated at: ' + str(datetime.datetime.now()).split('.')[0] + '</h4>')
    out.write('<table border = "1"><th>gold/system</th><th>' + '</th><th>'.join(vals) + '</th><th>Sum</th><th>Micro-recall</th>')
    doc = minidom.Document()
    matrix = doc.createElement('Matrix')
    doc.appendChild(matrix)
    for var in vals:
        Gs = doc.createElement('goldStandard')
        attr = doc.createAttribute('count')
        Gs.setAttributeNode(attr)
        Gs.setAttribute('count', var)
        matrix.appendChild(Gs)
        out.write('<tr><th>' + var + '</th>')
        total = []
        for val in vals:
            Eng = doc.createElement('Engine')
            attr = doc.createAttribute('count')
            Eng.setAttributeNode(attr)
            Eng.setAttribute('count', val)
            if (var, val) in data:
                value = doc.createTextNode(str(data[(var, val)]))
            else:
                value = doc.createTextNode('0')
            Eng.appendChild(value)
            Gs.appendChild(Eng)
            if val == var and not value.nodeValue == '0':
                current = value.nodeValue
                currentdi[val] = current
                out.write('<td bgcolor="#00CC33">' + value.nodeValue + '</td>')
            elif value.nodeValue == '0':
                out.write('<td bgcolor="#FFCC33">' + value.nodeValue + '</td>')
            else:
                out.write('<td bgcolor="#CC0000">' + value.nodeValue + '</td>')
            total.append(value.nodeValue)
        Summ = doc.createElement('sum')
        Sum = doc.createTextNode(str(sum([int(v) for v in total])))
        Summ.appendChild(Sum)
        Gs.appendChild(Summ)
        microrec = doc.createElement('Microrecall')
        try:
            mr = doc.createTextNode(str(Round(float(current)/float(Sum.nodeValue))))
        except:
            mr = doc.createTextNode('N/A')
        microrec.appendChild(mr)
        out.write('<td>' + Sum.nodeValue + '</td><td>' + mr.nodeValue + '</td</tr>')
    out.write('<tr><th>Sum</th><td>')
    Totals = []
    for var in vals:
        Totals.append(str(getTotal(var)))
    out.write('</td><td>'.join(Totals) + '</td></tr>')
    out.write('<tr><th>Micro-precision</th>')
    for var in vals:
        if not var in currentdi.keys():
            currentdi[var] = 0
        for i in currentdi:
            if i == var:
                try:
                    out.write('<td>' + str(Round((float(currentdi[i])/getTotal(var)))))
                except ZeroDivisionError:
                    out.write('<td>N/A')
    out.write('</td></tr></table>')
    out.write('<h4>Total correct: ' + str(sum(int(i) for i in currentdi.values())) + '</h4>')
    out.write('<h4>Total errors: ' + str(sum(errors.values())) + '</h4>')
    out.write('<h4>Total MIMs: ' + str(sum([int(i.firstChild.nodeValue) for i in doc.getElementsByTagName('sum')])) + '</h4>')
##    out.write('<h4>Accuracy: ' + str(Round(float(sum(int(i) for i in currentdi.values()))/sum([int(i.firstChild.nodeValue) for i in doc.getElementsByTagName('sum')]))))
    out.write('<h4>Number of documents: ' + str(numFiles/2) + '</h4>')
    out.write('<h3>List view:</h3>')
    out.write('<h4>True Positives:</h4><ul>')
    for i in getResults(tp):
        out.write('<li>' + i[0] + ' correctly identified as such ' + str(i[1]) + ' times.</li>')
    out.write('</ul><h4>Errors:</h4><ul>')
    errorlen = str(len(errors))
    docnum = 0
    sys.stdout.write('\nDumping the allmims object to file for future reuse...')
    pickle.dump(allmims, open(path + '\\allmims.txt', 'w'))
    sys.stdout.write(' Done!\n\n')
    for i in getResults(errors):
        docnum += 1
        sys.stdout.write('Creating error file ' + str(docnum) + ' out of ' + errorlen + '... ')
        errorAnalysis(i[0][0], i[0][1])
        if  i[1] == 1:
            out.write('<li>' + i[0][0] + ' mistakenly marked as ' + i[0][1] + ' ' + str(i[1]) + ' time.</li>')
        else:
            out.write('<li>' + i[0][0] + ' mistakenly marked as ' + i[0][1] + ' ' + str(i[1]) + ' times.</li>')
        sys.stdout.write(' Done!\n')
    out.write('</ul>')
    out.write('</body>')
    out.write('</html>')
print '\nConfusion matrix successfily generated.'
print '\nAll files successfuly written to ' + path
print 'Took', datetime.datetime.now()-startTime, 'to run', numFiles/2, 'files.'
