from lxml import etree
import os, ntpath, sys

path = sys.argv[1]           
#path = "...xslTransformers/"
#testdoc = "...beta\\temporality_RadiologyNeg\\engine\\..."

if not os.path.exists(path):
    raise Exception('Invalid path(s)')

if not os.path.exists(path + "\\retokenized"):
    os.makedirs(path + "\\retokenized")

docs = filter(lambda x: str(x.split('.')[len(x.split('.'))-1]) == 'xml' , os.listdir(path))

for doc in docs:
    print doc
    parser = etree.XMLParser(encoding="utf-8", recover=True)
    parsedDoc = etree.parse(path + "\\" + doc, parser=parser)
    orig = etree.XML(etree.tostring(parsedDoc))

    #XSLT transformation of parsed doc
    transform = etree.XSLT(etree.parse('C:\\Users\\courtney.zelinsky\\Desktop\\xslTransformers\\tokenizer.xsl'))
    outDoc = transform(parsedDoc)

    # Compare dom's of each of the original gs and retokenized gs
    origContexts = orig.xpath('//cda:content', namespaces={'cda':'urn:hl7-org:v3'})
    outputContexts = outDoc.xpath('*//content')

    narrBindings = orig.xpath('*//mm:narrativeBinding', namespaces={'mm':'http://mmodal.com/cdaExtensions'})

    for i in range(len(origContexts)):
        origContext = etree.XML(etree.tostring(origContexts[i]))
        outputContext = etree.XML(etree.tostring(outputContexts[i]))
        #print etree.tostring(outputContext) #up to 228
        if origContext.attrib['ID'] != outputContext.attrib['ID']:
            #if there's a narrative binding with an ID attribute matching the original document's ID attribute
            if outDoc.find('*//mm:narrativeBinding[@ref="' + origContext.attrib['ID'] +'"]/*[1]', namespaces={"mm":"http://mmodal.com/cdaExtensions"}) is not None:
                # replace the ID attribute of the original narrative binding with the ID attribute of the output, so as to coordinate MIM bindings with the new tokenization
                outDoc.find('*//mm:narrativeBinding[@ref="' + origContext.attrib['ID'] +'"]', namespaces={"mm":"http://mmodal.com/cdaExtensions"}).attrib['ref'] = outputContext.attrib['ID']
                continue
            else:
                continue

    f = ntpath.basename(doc)[:-4] + ".pyout." + ntpath.basename(doc)[-3:]
    with open(os.path.join(path + "\\retokenized", f), 'w') as output:
        output.write(etree.tostring(outDoc))
    output.close()

print("Retokenization complete! " + str(len(docs)) + " file(s) written to " + path + "\\retokenized")
