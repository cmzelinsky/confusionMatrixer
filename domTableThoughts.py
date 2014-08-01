# -*- coding: utf-8 -*-

from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element, tostring, SubElement, XML
import sys, os
import codecs

path = 'C:/Users/courtney.zelinsky/Desktop/deid'

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class TElement(ET._Element):
    
    def __init__(self, tag, style=None, text=None, tail=None, parent=None, attrib={}, **extra):
        ET._Element.__init__(self, tag, dict(attrib, **extra))
        
        if text:
            self.text = text
        if tail:
            self.tail = tail
        if style:
            self.style = style
        if not parent == None:
            parent.append(self)
            

data = {"MALE_NAME":{"MALE_NAME": 4, "LAST_NAME": 2},
        "LAST_NAME":{"MALE_NAME": 2, "LAST_NAME": 6}}


html = TElement('html')

table = TElement('table', parent=html)

headerRow = TElement('tr', parent=table)

tableHeaders = [ TElement('th', text=goldLabel) for goldLabel in confusionMatrix]

headerRow.extend(TElement('th', text="________", parent=headerRow))
headerRow.extend(TElement('th', text="engine:", parent=headerRow))
headerRow.extend(tableHeaders)

goldBlankRow = TElement('tr', parent=table)
goldBlankRow.extend(TElement('th', text= "gold stands:", parent=goldBlankRow))


for label in confusionMatrix:
    dataRow = TElement('tr', parent=table)
    rowHeader = TElement('th', text=label, parent=dataRow)
    blankData = TElement('td', parent=dataRow)
    for comparison in confusionMatrix[label]:
        comparisonData = [TElement('td', text=str(confusionMatrix[label][comparison])) for comparison in confusionMatrix[label]]
    dataRow.extend(comparisonData)

authorship = TElement('p', text="Email courtney.zelinsky@mmodal.com for questions / comments / suggestions for this script", parent=html)

# two ways:

output = prettify(html)

print(output)

with open(os.path.join(path, "outputFile.html"), 'w') as outputFile:
    outputFile.write(output)
    outputParsed = parse(os.path.join(path, "outputFile.html"))
    html = outputParsed.getElementsByTagName('html')
    html.appendChild('
outputFile.close()
