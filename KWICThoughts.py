# -*- coding: utf-8 -*-

from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element, tostring, SubElement, XML
from lxml import etree
import sys, os
import codecs

path = "C:/Users/courtney.zelinsky/Desktop/deid"
docs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml' , os.listdir(path))

def findPair(fname): 
    return fname[:-3] + 'out.xml'

truePositivesMaster = {"B~ClinicalDocument_2531456463.xml":{('entry_60', 'entry_61'): (u'ABSOLUTE_DATE',), ('entry_201', 'entry_202'): (u'ABSOLUTE_DATE',), ('entry_185', 'entry_186'): (u'ABSOLUTE_DATE',), ('entry_235', 'entry_236'): (u'ABSOLUTE_DATE',), ('entry_20', 'entry_21'): (u'ABSOLUTE_DATE',), ('entry_282',): (u'LAST_NAME',), ('entry_144', 'entry_145'): (u'ABSOLUTE_DATE',), ('entry_18', 'entry_19'): (u'ABSOLUTE_DATE',), ('entry_140', 'entry_141'): (u'ABSOLUTE_DATE',), ('entry_244', 'entry_245'): (u'ABSOLUTE_DATE',), ('entry_566',): (u'LOCATION',), ('entry_216', 'entry_217'): (u'ABSOLUTE_DATE',), ('entry_13', 'entry_14', 'entry_15'): (u'ABSOLUTE_DATE',), ('entry_85', 'entry_86'): (u'ABSOLUTE_DATE',), ('entry_131', 'entry_132'): (u'ABSOLUTE_DATE',), ('entry_256', 'entry_257'): (u'ABSOLUTE_DATE',), ('entry_388',): (u'LAST_NAME',), ('entry_8',): (u'LAST_NAME',), ('entry_271', 'entry_272'): (u'ABSOLUTE_DATE',), ('entry_7',): (u'FEMALE_NAME',), ('entry_228', 'entry_229'): (u'ABSOLUTE_DATE',), ('entry_70', 'entry_71'): (u'ABSOLUTE_DATE',), ('entry_285',): (u'AGE',), ('entry_103', 'entry_104'): (u'ABSOLUTE_DATE',)}}
#just using truePositives for testing here, but this will be the format
    
def KWIC(truePositivesMaster):
    for doc in truePositivesMaster:
        parsedDoc = minidom.parse(path + '\\' + doc)
        paragraphs = []
        output = []
        outputParagraph = []
        wordDict = {}
        paragraphs = parsedDoc.getElementsByTagName('paragraphs')
        contents = parsedDoc.getElementsByTagName('content')
        entryTuples = [entryTuples for entryTuples in truePositivesMaster[doc]]
        
        for content in contents:
            wordDict[content.getAttribute('ID')] = content.firstChild.nodeValue
        for entries in entryTuples:
            for entry in entries:
                for i in range(len(wordDict)):
                    entryTuple = []
                    if 'entry_' + str(i) == entry:
                        outputParagraph.append('<font style="background-color:yellow"><strong>' + wordDict['entry_' + str(i)] + '</strong></font>')
                    else:
                        outputParagraph.append(wordDict['entry_' + str(i)])
                output.append(outputParagraph)
                    #execute thusly: for each word in the paragraph (text node in //content), append it to $paragraphs
                    #if the text node is one whose parent's attribute ID is equal to the entry number i'm looping through,
                    #bold or somehow html-tag that corresponding text by appending it with sth like:
                    # <font style="background-color:yellow"><strong>' + w.firstChild.nodeValue + '</strong></font>
    print output
    print len(output)

KWIC(truePositivesMaster)

    #
    # HTML Output
    #

##    class TElement(ET._Element):
##    
##    def __init__(self, tag, style=None, text=None, tail=None, parent=None, attrib={}, **extra):
##        ET._Element.__init__(self, tag, dict(attrib, **extra))
##        
##        if text:
##            self.text = text
##        if tail:
##            self.tail = tail
##        if style:
##            self.style = style
##        if not parent == None:
##            parent.append(self)
##
##    root = TElement('root')
##    html = TElement('html', parent=root)
##
##    #Header
##    head = TElement('head', parent=html)
##
##    title = TElement('title', text="Deid Stats Results", parent=head)
##    css = TElement('link', parent=head)
##
##    css.attrib['href'] = "css.css"
##    css.attrib['type'] = "text/css"
##    css.attrib['rel'] = "stylesheet"
##
##    head.extend(css)
##    head.extend(title)
##
##    #Body
##
##    values = sorted([key for key in confusionMatrix.keys()])
##
##
##    body = TElement('body', parent=html)
##
##    h1 = TElement('h1', text="Deid Stats Results:", parent=body)
##
##    timeGenerated = TElement('p', text="Generated at: " + str(datetime.datetime.now()).split('.')[0], parent=body)
##
##    table = TElement('table', parent=body)
##
##    authorship = TElement('p', text="Email courtney.zelinsky@mmodal.com for questions / comments / suggestions for this script", parent=body)
##
##
##    # KWIC examination text to go here in html
##
##    # for the file it's hashed to, if some entry numbers appeared in false positives or false negatives, get all text descendents from paragraph nodes 
##
##    with open(os.path.join(path, ".html"), 'w') as outputFile:
##        for i in range(len(root)):
##            outputFile.write(ET.tostring(root[i]))
##    outputFile.close()
