import os, re

# Read file
filename = 'C:\Users\courtney.zelinsky\Desktop\Annotations-1-120.txt'

#mac:
#filename = '/Users/Courtney/Desktop/Annotations-1-120.txt'
f = open(filename, 'r+')


path = '\\'.join(filename.split('\\')[:-1])

#mac
#path = '/'.join(filename.split('/')[:-1])

if not os.path.exists(os.path.join(path, "corpus")):
    os.makedirs(os.path.join(path, "corpus"))

corpusList = f.read().split('\t')
del corpusList[:3]

docNum = 2
prevIndex = 0

for item in corpusList:
    if item.endswith('\n' + str(docNum)):
        currentIndex = corpusList.index(item)
        with open(os.path.join(os.path.join(path, 'corpus'), str(docNum-1)+'.txt'), 'w') as output:
            # Get the index of that item and make all words (items) up to that point become one string
            out = "\t".join(corpusList[prevIndex:currentIndex+1])
            output.write(out[out.index('\n')+1:])
        # Set that index as a variable so that can use it to reference the next spot where there is a changeover
        prevIndex = currentIndex
        docNum += 1
        #print docNum
    elif item.endswith('\n'+str(docNum+1)):
        currentIndex = corpusList.index(item)
        with open(os.path.join(os.path.join(path, 'corpus'), str(docNum)+'.txt'), 'w') as output:

            out = "\t".join(corpusList[prevIndex:currentIndex+1])
            output.write(out[out.index('\n')+1:])
        prevIndex = currentIndex
        docNum += 1
    elif item.endswith('\n119'):
        currentIndex = corpusList.index(item)
        with open(os.path.join(os.path.join(path, 'corpus'), '119.txt'), 'w') as output:
            out = '\t'.join(corpusList[prevIndex-1:])
            output.write(out[out.index('\n')+1:])
        break

outputContexts = []
index = 0
docCount = 0

if not os.path.exists(os.path.join(os.path.join(path, "corpus"), "plaintext")):
    os.makedirs(os.path.join(os.path.join(path, "corpus"), "plaintext"))

#Flattening the corpus to plaintext
for i in range(1, len(os.listdir(os.path.join(path, 'corpus')))+1):
    finalDocList = []
    if not str(i)+'.txt' in os.listdir(os.path.join(path, 'corpus')):
        continue
    elif str(i)+'.txt' in os.listdir(os.path.join(path, 'corpus')):
        Doc = open(os.path.join(os.path.join(path, 'corpus'), str(i)+'.txt'), 'r+').read()
        docList = Doc.split('\t')
        j = 0
        del docList[0::3]
        while j < len(docList):
            temp = docList[j+1].replace(docList[j].upper(), docList[j])
            docList[j+1] = temp
            j += 2
        with open(os.path.join(os.path.join(os.path.join(path, 'corpus'), 'plaintext'), str(i)+'_text.txt'), 'w') as sents:
            toWrite = [' '.join(item.split()) for item in docList[1::2]]
            for item in toWrite:
                if not item in finalDocList:
                    finalDocList.append(item)
            sents.write('\n'.join(finalDocList))
        sents.close()

# # # # # Then run through tokenization and other pipelines # # # # # 
