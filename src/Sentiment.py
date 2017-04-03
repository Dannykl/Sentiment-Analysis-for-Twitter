import nltk,pymysql,tweepy
import csv,re,string
from tweepy import OAuthHandler
from nltk.tokenize import RegexpTokenizer as pk
from nltk.corpus import stopwords as st
from nltk.tokenize import word_tokenize as tok
from nltk.stem import PorterStemmer as stemm
class Sentiment(object):
    global dataFromTwitter,replaceContraction,allWords
    global tokenizingAndRemovingPunctu,stemmingAndRemoveStopWords,vectorRepresentation
    global calculatingTheTerm,probabilityOfTheTerm,incrementNP,incrementPP,testingTheclassifier
    global labellingRetrievedData,readingTestDatabase,readingTrainingDatabase
    
    global numberNegativeDocument,numberPositiveDocument
    numberNegativeDocument = 0
    numberPositiveDocument = 0
    
    global inputFileInTheDatabase,readingDatabase,replaceContraction
    global userName,password,database,db,dbb
    password = ''
    userName = ''
    database =''
    db = ''
    dbb = ''
    
    def inputFileInTheDatabase():
        fileLocation = "dataset.csv"
        countPositive = 0 
        countNegative = 0
        global db
        try:
            read = csv.reader(open(fileLocation,encoding='Latin-1'))
        except IOError:
            print("File cannot be found")
        try:          
            db = pymysql.connect(db,userName,password,database)
            cur = db.cursor()
            for (i,a,b,c,d,e) in read:
            
                if((i[0] =='0')&(countNegative<=3750)):
                    cur.execute("INSERT INTO Training VALUES(%s,%s,%s,%s,%s,%s)",(i,a,b,c,d,e))
                if((i[0] =='0')&(countNegative > 3750)&(countNegative<=5000)):
                    cur.execute("INSERT INTO Test VALUES(%s,%s,%s,%s,%s,%s)",(i,a,b,c,d,e))
                if((i[0] == '4')&(countPositive >5000)&(countPositive<=8750)):
                    cur.execute("INSERT INTO Training VALUES(%s,%s,%s,%s,%s,%s)",(i,a,b,c,d,e))
                if((i[0] == '4')&(countPositive >8750)&(countPositive<=10000)):
                    cur.execute("INSERT INTO Test VALUES(%s,%s,%s,%s,%s,%s)",(i,a,b,c,d,e))
                countNegative +=1
                countPositive +=1
            db.commit()
            cur.close()
            db.close()
        except:
            print("CHECK MYSQL CONNECTION")
        

    def readingTrainingDatabase():
        global dbb
        a = []
        try:
            dbb = pymysql.connect(dbb,userName,password,database)
            c = dbb.cursor()
            c.execute("SELECT tweet,label FROM Training")   
            for w in c:
                a.append(w)
            dbb.commit()
            c.close()
            dbb.close()
        except:
            print("Mysql error for retrieve training")
            
        return replaceContraction(a)
    def readingTestDatabase():
        global db
        testList = []
        try:   
            db = pymysql.connect(db,userName,password,database)
            curs = db.cursor()
            curs.execute("SELECT tweet,label FROM Test")
            
            for w in curs:
                testList.append(w)
            db.commit()
            curs.close()
            db.close()
        except:
            print("Mysql error for retrieve test")
        return replaceContraction(testList)
    
    def dataFromTwitter():        
        fileLocation = 'retrievedWithDuplicate.csv'
        CONSUMER_KEY = ''
        CONSUMER_SECRET =  '' 
        language = 'en' #language of the tweets
        domain = '#lbc'#use domain specific for better result. Hashtag may be better
        lengthOfTweets = 3000 #how many tweets we want to retrieve
        auth = tweepy.auth.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        api = tweepy.API(auth)    
        
        resultsWithDup = []
        resultsWithoutDup = []
        
        for tweet in tweepy.Cursor(api.search, domain).items(lengthOfTweets):
            if(tweet.lang == language):
                #check tweepy parameters for twitter          
                resultsWithDup.append((tweet.user.name,tweet.user.id,tweet.text))          
        elementsInTheSet = set()
        for tt in resultsWithDup:
            if (tt[1] not in elementsInTheSet):
                resultsWithoutDup.append((tt[2],'2'))
                elementsInTheSet.add(tt[1])  
        removeNoise = []         
        for (t,s) in resultsWithoutDup:
            if (not t.startswith('RT'))|(not t.startswith('http')):
                removeNoise.append((t,s))
                print(t)
        return replaceContraction(removeNoise)
    def replaceContraction(b):
        #fileLocation = 'training.csv'
        cList = {
            "ain't": "am not", "can't've": "cannot have","'cause": "because",
            "could've": "could have","couldn't": "could not","couldn't've": "could not have", 
            "didn't": "did not","doesn't": "does not","i'm":"i am","don't":"do not","doesnt":"does not",
            "they've":"they have","there's":"there is","they'd":"they had","they'll":"they will",
            "they're":"they are","we'd":"we had","we're":"we are","we've":"we have","weren't":"were not",  
            "that's":"that is","it's":"it is","n't":"not","couldn't":"could not",
            "would've":"would have","I'll":"I will", "I've":"I have", "isn't":"is not",
            "let's	":"let us","mustn't":"must not","she'd":"she had","she'll":"she will",
            "she's":"she is","shouldn't":"should not","what'll":"what will","what're":"what are",
            "what's":"what is","what've":"what have","where's":"where is","who'd":"who had",
            "who'll":"who will","who's":"who is","who've":"who have","won't":"will not",
            "you'd"	:"you had","you'll":"you will","you're":"you are","you've":"you have",        
            "aren't": "are not","can't":"cannot","couldn't":"could not",
            "didn't":"did not","doesn't":"does not","don't":"do not",
            "hadn't":"had not","hasn't":"has not","haven't":"have not",
            "he'd":	"he had" ,"he'll":"he will","he's":"he is","I'd": "I would","dont":"do not"
     }
        R = re.compile('(%s)' % '|'.join(cList.keys()))
        #read = csv.reader(open(fileLocation))
        aList = []
        def expandContractions(text,R=R):
            def replace(match):
                return cList[match.group(0)]
            return R.sub(replace, text) 
        for (i,j) in b:
            aList.append((expandContractions(i.lower()),j))    
        return tokenizingAndRemovingPunctu(aList)
     
    def tokenizingAndRemovingPunctu(listWithoutContractions):
        newList = []
        for(tweet,label) in listWithoutContractions:
            removePunc =  ''.join([i for i in tweet if i not in (string.punctuation)])
            tokenizeWord = tok(removePunc)
            newList.append((tokenizeWord,label))
        return stemmingAndRemoveStopWords(newList)
    
    def stemmingAndRemoveStopWords(newList):  
        stemmer = stemm()
        newStemmedList = []
        stemmedList = []
        afterStopWord = []
        count = 0
        for(y,s) in newList:
            stemmedList = []
            for x in y:
                stemming = stemmer.stem(x)
                stemmedList.append(stemming)
            newStemmedList.append((stemmedList,s))
        #print(newStemmedList)
        
        listt = []
        for (a,b) in newStemmedList: 
            c = [
                    w for w in a if (w not in st.words('english'))&(len(w)>=3)
                ]
            afterStopWord.append((c,b))
        #print(afterStopWord)
        #return vectorRepresentation(afterStopWord)
        return afterStopWord
    
    def vectorRepresentation(allWords):          
        negative = {}
        positive = {}
        result = {}
        global numberNegativeDocument,numberPositiveDocument
        for (t,s) in allWords:
            if(s=='0'):
                numberNegativeDocument+=1
                for w in t:
                    if w in negative:
                        negative[w]+=1
                    else:
                        negative[w]=1
            if(s=='4'):
                numberPositiveDocument+=1
                for w in t:
                    if w in positive:
                        positive[w]+=1
                    else:
                        positive[w]=1
        for (key,value) in negative.items():
            try:
                result[key] = [value,positive[key]]
            except KeyError:
                result
        return probabilityOfTheTerm(result)
        #return result
        #calculatingTheTerm(result)
    def probabilityOfTheTerm(voca):
        vocaLength = len(voca)  #total vocabulary
        print(vocaLength)     
        countTermInNeg = 0 #the number of times the word accure in negative(n)
        countTermInPos = 0 #the number of times the word accure in positive(n)
        for(k,v) in voca.items():          
            countTermInNeg+= v[0]
            countTermInPos+= v[1]
            
        #print(countTermInNeg)
        #print(countTermInPos)
        numberNegativeDocument #numberofTheNegativeTweetsInTheDocument
        numberPositiveDocument #numberofThePositiveTweetsInTheDocument
        totalDocument = numberNegativeDocument + numberPositiveDocument #totalDocument
        
        #find out the number of times the word accur
        
        #print(numberNegativeDocument)
        #print(numberPositiveDocument)
        #print(totalDocument)
        probabNegativeDocument = numberNegativeDocument/totalDocument  #probability of negative tweets in all document
        probabPositiveDocument = numberPositiveDocument/totalDocument  #probability of positive tweets in all document
        #print(probabPositiveDocument)
        for (key,value)in voca.items():
            value[0]= (value[0] + 1)/(countTermInNeg+vocaLength)
            value[1]=(value[1]+1)/(countTermInPos+vocaLength)
            #print(value[0], " ,", value[1])
        #print(voca)
        #classifying(voca)
        return voca
    
    def testingTheclassifier(a,b):
        predictedAndActual = []
        positive = 4
        negative = 0
        count=0
        TP = 0 
        TN = 0
        FP = 0
        FN = 0
        for (tweet,C) in b:
            posPosterior = 0
            negPosterior = 0
            for word in tweet:
                found = False
                for(key,value) in a.items(): 
                    #print("key",key , "word ",word)
                    if(found==False):
                        if(word==key):
                            negPosterior += value[0]
                            posPosterior += value[1]
                            found = True
            
            #print("next tweet",count)
            if(posPosterior > negPosterior):
                #print("This sentence is positive",C)
                predictedAndActual.append([C,positive])
            if(posPosterior < negPosterior):
                #print("This sentence is negative",C)
                predictedAndActual.append([C,negative])
        for(actual,predicted) in predictedAndActual:
            #print(count ," actual:",actual,"" ,"Pridicted:",pridicted)
            
            if((actual=='0')&(predicted==0)):               
                TN+=1             
            if((actual=='4')&(predicted==4)):
                TP+=1
            if((actual=='0')&(predicted==4)):
                FP+=1
            if((actual=='4')&(predicted==0)):
                FN+=1
            count+=1
        print("TN:",TN," TP:", TP , " FP:",FP, " FN:",FN)
        total = TN+TP+FP+FN
        print(count, "Total:",total)
        
        accuracy = (TP+TN)/(total)
        precision = (TP)/(TP+FP) 
        recall = (TP)/(TP+FN)
        print("Accuracy: ",accuracy,"\n","precision:",precision,"\n","Recall:",recall)
        
        
        '''
                                 pridicted
                            positive   negative     total
       Actual   positive       TP        FN          P
                negative       FP        TN          N
                  
        accuracy = (TP + TN)/(P+N)
        error =(FP+FN)/(P+N)
        precision = (TP)/(TP+FP)
        recall = (TP)/(TP+FN)
        '''
    def labellingRetrievedData(training,r):
        negPosterior = 0
        posPosterior = 0
        positive = 4
        negative = 0
        found=False
        result = []
        for (t,s) in r:
            for term in t:
                for(key, value) in training.items():
                    if(found==False):
                        if(term==key):
                            negPosterior += value[0]
                            posPosterior += value[1]
                            found=True
            if(posPosterior > negPosterior):
                result.append((t,positive))
            if(posPosterior < negPosterior):
                result.append((t,negative))
        print(result)        
    def main():
        #inputFileInTheDatabase()
        #retrieved = dataFromTwitter()
        testList = readingTestDatabase()
        train = readingTrainingDatabase()
        
        training = {}
        test = {}
        training = vectorRepresentation(train)
           
        testingTheclassifier(training,testList)
        #labellingRetrievedData(training,retrieved)
 
    if __name__ == '__main__':
        main()
  