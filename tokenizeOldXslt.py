from lxml import etree
import os
import ntpath

#For doc in docs:
            
path = "C:/Users/courtney.zelinsky/Desktop/xslTransformers/"
doc = "C:\\Users\\courtney.zelinsky\\Desktop\\beta\\temporality_RadiologyNeg\\engine\\6970187.out.out.out.xml"
parser = etree.XMLParser(encoding="utf-8", recover=True)
parsedDoc = etree.parse(doc, parser=parser)
orig = etree.XML(etree.tostring(parsedDoc))

#XSLT transformation of parsed doc
transform = etree.XSLT(etree.parse('C:\\Users\\courtney.zelinsky\\Desktop\\xslTransformers\\tokenizer.xsl'))
outDoc = transform(parsedDoc)

#print etree.tostring(outDoc, pretty_print=True)

f = ntpath.basename(doc)[:-4] + ".pyout." + ntpath.basename(doc)[-3:]
with open(os.path.join(path, f), 'w') as output:
    output.write(etree.tostring(outDoc))
output.close()

# Compare dom's of each of the original gs and retokenized gs
origContexts = orig.xpath('//cda:content', namespaces={'cda':'urn:hl7-org:v3'})
outputContexts = outDoc.xpath('*//content')

for i in range(len(outputContexts)):
    #think about using attrib somehow?
    print "orig: ", origContexts[i].xpath('*//cda:.[@ID="entry_' + str(i) + '"]', namespaces={'cda':'urn:hl7-org:v3'})
    print "output: ", outputContexts[i].xpath('*//.[@ID="entry_' + str(i) + '"]')
    if origContexts[i].xpath('*//cda:content[@ID="entry_' + str(i) + '"]', namespaces={'cda':'urn:hl7-org:v3'}) != outputContexts[i].xpath('*//content[@ID="entry_' + str(i) + '"]'):
        print "difference found:"
        print "orig: ", origContexts[i].xpath('*//cda:content[@ID="entry_' + str(i) + '"]', namespaces={'cda':'urn:hl7-org:v3'})
        print "output: ", outputContexts[i].xpath('*//content[@ID="entry_' + str(i) + '"]')
        #print etree.tostring(elem), etree.tostring(retokElem)
            # 1 - collect elem's ID attribute in a var
            # 2 - change elem's ID attrribute to be retokElem's entry number
            # 3 - if there are any ref attributes of narrativeBinding that are equal to the elem ID attribute value,
            #     change it to be the retokElem's ID attribute value
    else:
        print "match, continuing"
        continue
