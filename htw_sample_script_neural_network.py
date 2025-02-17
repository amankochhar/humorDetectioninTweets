from __future__ import print_function

import os
import sys
import csv
import itertools
import numpy as np
from random import random
from sklearn.neural_network import MLPClassifier
from collections import defaultdict
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction import DictVectorizer
# Aashish 
import re
import time
import nltk
import string
import subprocess
from nltk.stem import WordNetLemmatizer
#Prudhvi
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag,pos_tag_sents

all_tweets = [] #Global list of all parsed tweets 
wnl = WordNetLemmatizer()

class SupervisedExpRunner(object):
    def __init__(self):
        self.model = None

    def _create_classifier(self):
        self.model = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(5, 2), random_state=1)

    def _fit(self, X, y):
        if self.model is None:
            self._create_classifier()

        self.model.fit(X, y)

    def _evaluate(self, X, y):
        y_pred = self.model.predict(X)
        acc = accuracy_score(y, y_pred)
        self.results = {'accuracy': acc}

    def _separate_data(self, X, y):
        X_win = X[y == 2]
        X_top10 = X[y == 1]
        X_rest = X[(y != 1) & (y != 2)]

        return X_win, X_top10, X_rest

    def _create_pairwise_data(self, Xs, ys, in_dv):
        ## Xs = token freq and ys = labels for tweets per file
        ## both the params are lists of lists divided internally by files
        ## Xs[i] = the list of tweets from the first file in our corpus and so on
        X_pairs = []
        y_pairs = []
        for X, y in zip(Xs, ys):
            # separating our tweets on the basis of the label data
            X_win, X_top10, X_rest = self._separate_data(in_dv.transform(X), y)
            # comparing winning tweet with the top 10
            for tweet_pair in itertools.product(X_win, X_top10):
                if random() > 0.5:
                    tweet_data = np.hstack((tweet_pair[0], tweet_pair[1]))
                    tweet_label = 1
                else:
                    tweet_data = np.hstack((tweet_pair[1], tweet_pair[0]))
                    tweet_label = 0

                X_pairs.append(tweet_data)
                y_pairs.append(tweet_label)

            # comparing top 10 with rest of the tweets
            for tweet_pair in itertools.product(X_top10, X_rest):
                if random() > 0.5:
                    tweet_data = np.hstack((tweet_pair[0], tweet_pair[1]))
                    tweet_label = 1
                else:
                    tweet_data = np.hstack((tweet_pair[1], tweet_pair[0]))
                    tweet_label = 0

                X_pairs.append(tweet_data)
                y_pairs.append(tweet_label)

            # comparing winning tweet with the rest of the tweets 
            for tweet_pair in itertools.product(X_win, X_rest):
                if random() > 0.5:
                    tweet_data = np.hstack((tweet_pair[0], tweet_pair[1]))
                    tweet_label = 1
                else:
                    tweet_data = np.hstack((tweet_pair[1], tweet_pair[0]))
                    tweet_label = 0
                # X is a list of list of all the tweets in our Xs
                # Y is the label data for all the tweets 
                X_pairs.append(tweet_data)
                y_pairs.append(tweet_label)

        X = np.vstack((X_pairs))
        y = np.array(y_pairs)
        # X is a list of list with each tweet transformed into a number vector of features
        return X, y

    def get_results(self):
        return self.results

    def run_loo_exp(self, Xs, ys, ht_list, ow_name = 'results'):

        # # Xs = X_bow i.e the token freq of our corpus
        # # ys = labels of our file
        # # ht_list = file name (we separate everything based on the file name)
        # print(Xs)
        # print(ys)

        out_file = open(ow_name+'.csv', 'w')
        ow = csv.writer( out_file )
        micro_sum = 0
        total_pairs = 0
        num_hts = len(ys) # number of files in our data
        for i in range(num_hts):
            print(str(100*i/num_hts)+'% done')
            # leave one out model
            # basically train on all (except one) and test on it
            
            # all our features divided into test and training data
            Xs_test = [Xs[i]]
            ys_test = [ys[i]]
            Xs_train = Xs[:i] + Xs[i+1:] # first i and all but first i + 1
            ys_train = ys[:i] + ys[i+1:]

            dv = DictVectorizer(sparse=False)
            dv.fit([tweet for hashtag in Xs_train for tweet in hashtag])

            # print("Xs_train",Xs_train)
            X_train, y_train = self._create_pairwise_data(Xs_train, ys_train, dv)
            # print("X_train", y_train, X_train)
            X_test, y_test = self._create_pairwise_data(Xs_test, ys_test, dv)

            # fitting the svm model
            self._fit(X_train, y_train)
            self._evaluate(X_test, y_test)
            ht_result = self.get_results()
            ow.writerow([ht_list[i], str(ht_result['accuracy'])])
            micro_sum += ht_result['accuracy'] * y_test.shape[0]
            total_pairs += y_test.shape[0]
            self.model = None
        out_file.close()
        print('100% done')
        return micro_sum / total_pairs

#########################
### Functions ###########
#########################
# adding the added features to the dataset
def create_bow_rep(in_tweet, profFreq, puncFreq, lenPerTweet, rhymeFreq, context):
    # print(profFreq, puncFreq, lenPerTweet)
    # pos already in the data
    #Adding Brett's features -------------------->
    profFreqKey = profFreq.keys()
    profFreqValue = profFreq.values()
    puncFreqKey = puncFreq.keys()
    puncFreqValue = puncFreq.values()
    lenPerTweetKey = lenPerTweet.keys()
    lenPerTweetValue = lenPerTweet.values()
    rhymeFreqTweetKey = rhymeFreq.keys()
    rhymeFreqTweetValue = rhymeFreq.values()
    contextKey = context.keys()
    contextValue = context.values()
    # ------------------------------------>
    bow_map = defaultdict(int)
    tokens = in_tweet.split()
    for tok in tokens:
        bow_map[tok] += 1
    #Brett's features--------------------->
    bow_map[profFreqKey[0]] = profFreqValue[0]
    bow_map[puncFreqKey[0]] = puncFreqValue[0]
    bow_map[lenPerTweetKey[0]] = lenPerTweetValue[0]
    bow_map[rhymeFreqTweetKey[0]] = rhymeFreqTweetValue[0]
    bow_map[contextKey[0]] = contextValue[0]
    # ------------------------------------>
    # print(bow_map)
    return bow_map
    

def load_hashtag(data_location, htf):
    ## we load each file save the tweets in the tweet list and create X_bow from it
    ## Also we use the labels from each file to create Y which is a numpy array to store all the labels in
    tweets = []
    labels = []
    for line in open(os.path.join(data_location,htf)).readlines():
        line_split = line.strip().split('\t')
        parse_tweets(line_split) #Call the parser on each line (For Brett's parse_tweets function)
        ## each list has one hashtag
        tweets.append(line_split[1])
        ## each list has one hashtag
        labels.append(int(line_split[2]))
    #--------------------------------------------------------------->
    # magic
    # cleaning the tweets by removing hashtags and usernames
    cleaned = cleanData(tweets)
    # creating the rhymefreq to add to our model
    rhymeFreq = createFeaturedList_Rhyme(cleaned, False, htf)
    # print(rhymeFreq)
    context = runContextFeature(tweets, htf)
    # print(context)
    # Parts of speech tagging
    poS = clean_for_pos_tag(cleaned)
    # getting the punctuation, profanity and the length of the tweets per file
    profFreq, puncFreq, lenPerTweet = create_features_for_file(htf,tweets)
    #X_bow = tweets
    Y = np.array(labels)

    # we are using the tweets data that already had the POS attached to each word to create the bow
    X_bow = []
    for i in range(0, len(tweets)):
        X_bow.append(create_bow_rep(tweets[i], profFreq[i], puncFreq[i], lenPerTweet[i],rhymeFreq[i], context[i]))

    # print("X_bow", X_bow)
    return {'X_bow':X_bow,'Y':Y}


def create_data(data_location):
    ht_files = sorted(os.listdir(data_location))

    Xs = []
    ys = []
    ht_list = []

    print("Loading Files")
    progress = 100/len(ht_files)
    count = 1
    print("Extracting Features Progress: 0 %", )
    for htf in ht_files:
        # sending each file one by one for structuring of our data
        ht_dict = load_hashtag(data_location,htf)
        ht_list.append(htf)
        ys.append(ht_dict['Y'])
        Xs.append(ht_dict['X_bow'])
        
    ## we now have the name of the file with the token freq and label info
        print("Extracting Features Progress:", progress*count, "%", )
        count += 1
    return Xs, ys, ht_list


# Aashish -- rhyming words and freq-------------------------------------------->

def cleanData(tweet):

    #Any necessary data cleaning should be performed here. Removes midnight, hashtags and any punctuations
    cleanedList = []
    r = re.compile(r"([#@])(\w+)\b")
    for lines in tweet:
        lines  = r.sub('',lines)    
        lines= lines.translate(None, string.punctuation)        
        cleanedList.append(lines)
    return cleanedList


# def createFeaturedList_Rhyme(tweetsList,combineHashRhymeInformation,filename):
    
#     #tweetsList : List of tweets in a file
#     #combineHashRhymeInformation : Flag if to consider rhyming with hashtag
#     #filename : List of words in the hashtag. Comes from the filename

#     featuredRhymeList= []
#     featuredFrequencyList = []

#     ##New Change...........
#     key = filename.split('.')[0] + "_" + `len(tweetsList)` + "_" + "Rhyme"

#     for i in range(len(tweetsList)):
#         frequencyElement = 0
#         selectedPair = []
#         tweet = tweetsList[i]

#         #Separates the word/token from the individual tweet
#         tokens = nltk.word_tokenize(tweet)

#         #Loop thru unique tokens
#         for token in set(tokens):

#             #Check each token if rhymes with all other tokens in that tweet
#             rhymingpairs  = isRhyming(token,tokens)

#             if(len(rhymingpairs) > 0 ):
#                 selectedPair.extend(rhymingpairs)

#             if(combineHashRhymeInformation):
#                 rhymingPairs = isRhyming(token,nltk.word_tokenize(filename))
#                 if (len(rhymingpairs)>0):
#                     selectedPair.extend(rhymingpairs)

#         if(len(selectedPair)==0):
#             emptyList = ['NULL_NULL']
#             featuredRhymeList.append(emptyList)
#             featuredFrequencyList.append(0)
#         else:
#             featuredRhymeList.append(selectedPair)
#             featuredFrequencyList.append(len(selectedPair))
#     ## Creating Dictionary
#     frequencyDict = {filename : featuredFrequencyList}
#     rhymingDict = {key : featuredRhymeList}
#     return rhymingDict #featuredFrequencyList #featuredRhymeList #featuredFrequencyList      

def createFeaturedList_Rhyme(tweetsList,combineHashRhymeInformation,filename):
    #tweetsList : List of tweets in a file
    #combineHashRhymeInformation : Flag if to consider rhyming with hashtag
    #filename : List of words in the hashtag. Comes from the filename

    #print tweetsList

    # featuredRhymeList= []
    # featuredFrequencyList = []
    # key = filename.split('.')[0] + "_" + `len(tweetsList)` + "_" + "Rhyme"
    
    
    
    freqDictList = []

    for i in range(len(tweetsList)):
        frequencyElement = 0
        selectedPair = []
        frequencyDict = {}
        rhymingDict = {}
        tweet = tweetsList[i]
        featuredRhymeList= []
        featuredFrequencyList = []
        key = filename.split('.')[0] + "_" + `i` + "_" + "Rhyme"
    
        #Separates the word/token from the individual tweet
        tokens = nltk.word_tokenize(tweet)

        #Loop thru unique tokens
        for token in set(tokens):

            #Check each token if rhymes with all other tokens in that tweet
            rhymingpairs  = isRhyming(token,tokens)

            if(len(rhymingpairs) > 0 ):
                selectedPair.extend(rhymingpairs)

            if(combineHashRhymeInformation):
            
                rhymingPairs = isRhyming(token,nltk.word_tokenize(filename))
                if (len(rhymingpairs)>0):
                    selectedPair.extend(rhymingpairs)

        #print 'For tweet ' , tweet , ' total pairs of rhyming are ' , len(selectedPair)

        if(len(selectedPair)==0):
            emptyList = ['NULL_NULL']
            #featuredRhymeList.extend(emptyList)
            count = 0
        else:
            count = len(selectedPair)
            #featuredRhymeList.extend(selectedPair)
            #featuredFrequencyList.append(len(selectedPair))

        frequencyDict[key] = count
        rhymingDict[key] = featuredRhymeList
        freqDictList.append(frequencyDict)
        
    # print (frequencyDict)

 ## Creating Dictionary
 ##frequencyDict = {key : featuredFrequencyList}
       ## rhymingDict = {key : featuredRhymeList}
       ## print(rhymingDict)
    return freqDictList        

def rhyme(inp, level):
    #returns the list of words that is rhyming with the word inp . Level is the rhyming detail we want to consider. 
    #This program uses the level as 1.
    entries = nltk.corpus.cmudict.entries()
    syllables = [(word, syl) for word, syl in entries if word == inp]
    rhymes = []
    for (word, syllable) in syllables:
        rhymes += [word for word, pron in entries if pron[-level:] == syllable[-level:]]
    return set(rhymes)

def isRhyming( word1, word2):
    rhymingPairs = []
#Finds if the word- word1 is rhyming with any of the words in word2 list
    rhymingSet = rhyme(word1,2)

    
    for w in set(word2):                
        if(word1.find (w) != (len(word1) - len(w)) and w.find(word1)!=(len(w) - len(word1))):
            if(w in rhymingSet):
                s = [word1,'_',w]
                newElement = "".join(s)
                rhymingPairs.append(newElement)
    return rhymingPairs

def runScript(word):
    #Run demo-script from word2vec tool with a word from the hashtag. Code in that script is modified to accept a parameter
    cmd= './word2vec-master/scripts/runWordToVec.sh ' +  word + ''
    subprocess.call(cmd,shell=True)
    time.sleep(3)


def generateContext(filename) :

    #Generate Context list and append to a file for all the words in the hashtag that has length > 3
    words= []
    file = filename.split('.')[0]
    words.extend(file.split('_'))

    for word in words:
        if(len(word) > 3):
            runScript(wnl.lemmatize(word.lower()))


def getContextFromFileandDelete(filePath):

    #Creates a list of all the context from the output file and deletes the file
    context=[]

    with open(filePath) as f:
        
        for line in open(filePath):
            values = line
            for value in values.split('_'):
                lValue = wnl.lemmatize(value)
                context.extend(wnl.lemmatize(lValue))
    os.remove(filePath)
    return context

def generateFeatureSet(context, tweetsList, filename):

    #Main method for creating the feature set.Counts the number of words within the context in a given tweet and creates a feature list
    
    i = 0;
    freqDictList = []
 
    for tweets in tweetsList:
        featureList = []
        featureDict = {}
        count = 0
        key = filename.split('.')[0] + "_" + `i` + "_" + "Context"
        for iWord in nltk.word_tokenize(tweets):
            # Only consider words with length more than 3 to prevent most determiners and numbers (stop words)
            if(len(iWord) > 3):
                if(wnl.lemmatize(iWord.lower()) in context):
                    count = count + 1
                    #print iWord.lower()
        featureDict[key] = count
        freqDictList.append(featureDict)
        i = i+1;

    return freqDictList;    

def runContextFeature(tweetsList,filename):

    #First Method to be called for running this script with tweets list and filename as parameters.

    output = open("context.out", 'w')
    generateContext(filename)
    context = getContextFromFileandDelete("context.out")
    featuredDict = generateFeatureSet(context,cleanData(tweetsList),filename)

    return featuredDict 

# Aashish methods end ------------------------------------------------------>
# Prudhvi methods for POS--------------------------------------------------->

def tokenize(line):
    tokens = word_tokenize(line)
    return tokens

def tag_POS(process_pos):
    return pos_tag_sents(process_pos)

def clean_for_pos_tag(tweet):
    process_pos = []
    tweetsPOS = []

    for line in tweet: 
        line = tokenize(line)
        #cleaning token here
        line = [i for i in line if i != ',' and i != '!' and i != ':' and i != '...' and i != '.' and i != ';' and i != '(' and i != ')' and i != ':' ] #cleaning token here
        process_pos.append(line) 
    pos = tag_POS(process_pos)
    for sentence in pos:
        temp = ()
        for words in sentence:
            newSentence = '_'.join(words)
            temp += (newSentence, )
        res = ' '.join(temp)
        tweetsPOS.append(res)

    return(tweetsPOS) 

# Prudhvi methods end ------------------------------------------------------>

# Brett Methods starts------------------------------------------------------->
#Finalizes global list of all tweets, gets called in load_hashtag()
def parse_tweets(line_split):
    global all_tweets
    all_tweets.append(line_split)

#Parses an individual tweet
def parse_individual_tweet(id):
    tweet_text = id
    return tweet_text
    
#Counts the number of occurrences of profanity in a tweet
def count_profanity(id):
    tweet_text = parse_individual_tweet(id) #Parse the tweet fields
    #Count the profanity by seeing if there is an occurence of each possible profanity in the profanity dictionary
    profanity_count = 0
    profanity_list = [line.strip() for line in open("en",'r')]
    for element in profanity_list:
        profanity = str(element)    
        pattern = re.compile(r"(.)(" + re.escape(profanity) + ")(.*)",re.IGNORECASE)
        matches = re.findall(pattern,tweet_text)
        count = len(matches)
        profanity_count += count
    return profanity_count

#Counts the number of punctation marks in a tweet
def count_punctuation(id):
    tweet_text = parse_individual_tweet(id) # Parse the tweet fields
    punctuation_count = 0
    #Count number of occurrences of each punctuation, one per line for readability
    punctuation_count += tweet_text.count('"')
    punctuation_count += tweet_text.count(':')
    punctuation_count += tweet_text.count(',')
    punctuation_count += tweet_text.count('-')
    punctuation_count += tweet_text.count('?')
    punctuation_count += tweet_text.count('(')
    punctuation_count += tweet_text.count(')')
    punctuation_count += tweet_text.count('[')
    punctuation_count += tweet_text.count(']')
    punctuation_count += tweet_text.count('.')
    punctuation_count += tweet_text.count('?')
    punctuation_count += tweet_text.count('"')
    punctuation_count += tweet_text.count(';')
    return punctuation_count

# Counts the length of a tweet
def count_length(id):
    tweet_text = parse_individual_tweet(id) # Parse the tweet fields
    length_count = len(tweet_text)
    return length_count
 
def create_features_for_file(filename,tweet_list):
    #Initialize the lists
    profanity_list = []
    punctuation_list = []
    length_list = []
    #For each tweet in the dataset
    i=0
    for each in tweet_list:
        #Initialize the dictionaries
        profanity_feature = {}
        #Parse the tweet id
        the_id = str(each)
        #Use the tweet to call all the count functions
        profanity_count = count_profanity(the_id)
        #Create dictionaries for each feature
        key_string = str(filename)+"_profanity_"+str(i)
        profanity_feature[key_string] = profanity_count
        #Add the feature to the list
        profanity_list.append(profanity_feature)
        i=i+1
    #For each tweet in the dataset
    j=0
    for each in tweet_list:
        #Initialize the dictionaries
        punctuation_feature = {}
        #Parse the tweet id
        the_id = str(each)
        #Use the tweet to call all the count functions
        punctuation_count = count_punctuation(the_id)
        #Create dictionaries for each feature
        key_string = str(filename)+"_punctuation_"+str(j)
        punctuation_feature[key_string] = punctuation_count
        #Add the feature to the list
        punctuation_list.append(punctuation_feature)    
        j=j+1
    #For each tweet in the dataset
    k=0
    for each in tweet_list:
        #Initialize the dictionaries
        length_feature = {}
        #Parse the tweet id
        the_id = str(each)
        #Use the tweet to call all the count functions
        length_count = count_length(the_id)
        #Create dictionaries for each feature
        key_string = str(filename)+"_length_"+str(k)
        length_feature[key_string] = length_count
        #Add the feature to the list
        length_list.append(length_feature)
        k=k+1
    return profanity_list, punctuation_list, length_list

# Brett Methods end -------------------------------------------------------->
#########################
### Main ################
#########################
def main():
    if len(sys.argv) != 2:
        print('Usage:', __file__, '<data_dir>')
        print(' ','data_dir:','\t','the path to the directory that contains the hahstag data files')
        sys.exit(1)

    data_location = sys.argv[1]
    ## Xs = X_bow i.e the token freq of our corpus. Data structure = list of dictionaries, every tweet is a dict
    ## ys = labels of our file data struture = np arrays
    ## ht_list = file name (we separate everything(tweets and labels) based on the file name)
    print("Starting Task")
    Xs, ys, ht_list = create_data(data_location)
    print("Fatures Extracted. Training Model")
    exp_runner = SupervisedExpRunner()
    outwriter_name = 'results_sem'
    results = exp_runner.run_loo_exp(Xs, ys, ht_list, outwriter_name)
    print('micro-avergae accuracy:',results)


if __name__ == '__main__':
    main()
