# humorDetectioninTweets

Please read the README.pdf for extensive walkthrough on how to run the model.
This code has been modified from the skeleton code provided by the SemEval task. We have worked with four different models and many different features. These different models and all these features have increased the accuracy from 49% to 70% for the Naive Bayes model.

About this folder
-----------------
This folder contains 
1) a directory that conatins the trial data, which consists of five hashtag files
2) a sample script to run experiments on the trial data.

Trial and Training Data
-----------------------

The training/trial data consits of a single directory with several files. Each file corresponds to a single hashtag, and is named appropriately. 
For example, for the hashtag #FastFoodBooks, the file is called Fast_Food_Books.tsv. We add the underscore between hashtag tokens for easier 
parsing of the hahstags. We believe a better semantic understanding of the hashtag will contribute to a better performance in the task.

The tweets are labeled 0, 1, or 2. 0 corresponds to a tweet not in the top 10 (most of the tweets in a file). 
1 corresponds to a tweet in the top 10, but not the winning tweet (usually, 9 tweets per hashtag). 
2 corresponds to the winning tweet (one tweet per hashtag).

Data Format
----------

The hashtag files contain three tab-separated columns:
tweet_id tweet_text tweet_label

Sample Script
------------

Dependencies:
NLTK
Numpy
Scikit-learn

The sample script gives an idea of how to use the trial/training data. The sample script performs leave-one-out experiments on the hashtag files in the directory given as an argument to the script. Example usage:

$ python model.py small_data

Specifically, the script holds-out one hashtag file at a time out. It then forms appropraite tweet pairs within the remaining (training) hashtag files. Indiviadual tweet representation is BOW frequency. The label applied to a tweet pair corresponds to whether or not the first tweet in the pair is the funnier tweet. The ordering of the pairs is random, and is chosen by a coin-flip. These pairs are then combined across all the training files to create the training matrix. An SVM model is trained on the resulting training matrix. Tweet pairs are also formed from the held-out hashtag file, and accuracy is computed on the resulting test matrix. The script reports micro-avergae accruacry across all held-out files, since different files have different amounts of tweets.

Evaluation data
---------------

For evaluation, tweets with different labels will be paired, and the goal will be to determine which tweet is the funnier. We ask that participant do not use the knowledge of label distributions directly when creating their systems. Evaluation will take place on previously unreleased hashtag files. Therefore an effective system will be able to generalize to new hashtags. We recommend to perform leave-one-out evaluation of the training files to determine the overall performance of a given system.