from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element, tostring, SubElement, XML

# python 3.3.2 tested

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class TElement(ET._Element):
    def __init__(self, tag, text=None, tail=None, parent=None, attrib={}, **extra):
        ET._Element.__init__(self, tag, dict(attrib, **extra))

        if text:
            self.text = text
        if tail:
            self.tail = tail
        if not parent == None:
            parent.append(self)

data = {"MALE_NAME":{"MALE_NAME": 4, "LAST_NAME": 2},
        "LAST_NAME":{"MALE_NAME":2, "LAST_NAME":6}}


html = TElement('html')
table = TElement('table', parent=html)


tableHeaders = [ TElement('th', text=goldLabel) for goldLabel in data]

tableRows = [ TElement('tr', text=goldLabel) for goldLabel in data]

table.extend(tableHeaders)
table.extend(tableRows)

##table = outputDoc.getElementsByTagName("table")
##
##iterator = 0
##
##for goldLabel in data:
##    iterator += 1
##    table.item(iterator).appendChild('th')
##    outputDoc.getElementsById(iterator).appendChild(goldLabel)
##    if iterator > len(data):
##        for i in range(iterator-1):
##            table.appendChild('tr')
##            outputDoc.getElementsById('tr').appendChild(goldLabel)

# two ways:

ET.dump(html)

print(prettify(html))

ET.write('output.xml')
