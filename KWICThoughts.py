def getTextForKWIC(data):
    '''- Intake a nested dict of {filename:{gsLabel:{engineLabel:entryNums, ...}, ...} ...}
       - For all data other than TPs (i.e. the errors), generate a KWIC listing
       - Output this to the generated confusionMatrix-deid.html file 
    '''
    doc = minidom.parse(path + '\\' + fname)
    docTemp = ET.parse(path + '\\' + fname)
    concept = []
    text = []
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
    para = '<span onclick="showHide(this)" style="cursor:pointer">Context <span class="plusMinus">[+]</span></span><br><span style="display:none">' + ''.join(text) + '</span>'
    print fname + separator + concept + separator + text
