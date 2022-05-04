import argparse
import json
import re
import csv
import gzip
import pickle
import logging
import random
from gensim.models import LdaModel
from gensim.corpora import Dictionary
import numpy

if __name__ == "__main__":
# '''
# current command example:
# python3 /Users/mingzhang/Desktop/spring2022/cdh/train_apply_topic.py
# --model /Users/mingzhang/Desktop/spring2022/AS.100.682/covidtry 
# --input /Users/mingzhang/Desktop/spring2022/cdh/covid_tweets.json.gz 
# --output /Users/mingzhang/Desktop/spring2022/AS.100.682/covidtry.json
# --topic_result /Users/mingzhang/Desktop/spring2022/AS.100.682/covid_topics
# --term_result /Users/mingzhang/Desktop/spring2022/AS.100.682/covid_terms
# --dict_vocab /Users/mingzhang/Desktop/spring2022/AS.100.682/covid_vocab
# '''
    parser = argparse.ArgumentParser()
    # Files with essential info
    parser.add_argument("--input", dest="input", help="Input file")
    parser.add_argument("--model", dest="model", help="Model file")
    parser.add_argument("--output", dest="output", help="Output file")
    parser.add_argument("--topic_result", dest="topic_result", help="topic_result file")
    parser.add_argument("--term_result", dest="term_result", help="term_result file")
    parser.add_argument("--dict_vocab", dest="dict_vocab", help="dict_vocab file")

    # Currently not used (could be user choice)
    parser.add_argument("--topic_count", dest="topic_count", default=20, type=int)
    parser.add_argument("--text", dest="text")
    # Could choose other info to keep, e.g. doc['user']['created_at'] in Twitter dataset, User needs to locate this info in json
    # Details in text processing (could be user choice)
    parser.add_argument("--lower_case", dest="lower_case", type=int, default=0)
    parser.add_argument("--keep_punctuation", dest="keep_punctuation", type=int, default=0)
    parser.add_argument("--max_doc_length", dest="max_doc_length", type=int)
    # Training details
    parser.add_argument("--passes", dest="passes", default=20, type=int)
    parser.add_argument("--iterations", dest="iterations", default=100, type=int)
    parser.add_argument("--random_seed", dest="random_seed", default=0, type=int, help="Random seed")
    # Others
    parser.add_argument("--log_level", dest="log_level", default="INFO",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], help="Logging level")
    args = parser.parse_args()
    # logging.basicConfig(level=args.log_level)
    random.seed(args.random_seed)
    numpy.random.seed(args.random_seed)
 
    # Collect tokenized docs to train on
    docs = []
    with gzip.open(args.input, "r") as ifd:
        for line in ifd:
            item = json.loads(line)
            text = item.get("text", "")
            text = text.lower()
            text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
            text = text.split()
            if len(docs) == 3000: # decide the amount of docs to train on --> 改random
                break
            docs.append(text)

    # Train and save model
    dictionary = Dictionary(docs)
    dictionary.filter_extremes(no_below=0.005, no_above=0.5)
    corpus = [dictionary.doc2bow(doc) for doc in docs]
    model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=args.topic_count,
        alpha="auto",
        eta="auto",
        iterations=args.iterations,
        passes=args.passes,
        eval_every=None
    )
    model.save(args.model)
    with open(args.model+'.pickle', 'wb') as handle:
        pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # with open(args.model+'.pickle', 'rb') as handle:
    #     b = pickle.load(handle).decode('utf-8')
    # with gzip.open(args.model+'.pickle.gz', "wt") as ofd:
    #         ofd.write(pickle.dumps(b, protocol=pickle.HIGHEST_PROTOCOL))
    
    # Save dictionary
    with open(args.dict_vocab, "wt") as ofd:
        c = csv.writer(ofd, delimiter="\t")
        for v in dictionary:
            c.writerow([dictionary[v]])

    # Save topics with their top words
    topics = model.show_topics(num_topics=model.num_topics, formatted=False)
    with open(args.topic_result, "wt") as ofd:
        c = csv.writer(ofd, delimiter="\t")
        for topic_num, topic_terms in topics:
            c.writerow([w + ' '+ str(float(p)) for w, p in topic_terms])

    # Save words with their top topics
    with open(args.term_result, "wt") as ofd:
        c = csv.writer(ofd, delimiter="\t")
        for i in range(len(dictionary)):
            c.writerow([str(t) + ' '+ str(float(p)) for t, p in model.get_term_topics(i)])


    # Apply model to each doc and only keep interesting info in each doc
    docs_complete = []
    with gzip.open(args.input, "rt") as ifd, gzip.open(args.output, "wt") as ofd:
        for line in ifd:
            item = json.loads(line)
            text = item.get("text", "")
            text = text.lower()
            text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
            text = text.split()
            # add topic modeling info to each doc
            document_topics = model.get_document_topics(model.id2word.doc2bow(text),per_word_topics=True)
            topics = {k : float(v) for k, v in document_topics[0]}
            # per_word_topics = {dictionary[k] : v for k, v in document_topics[1]}
            document_topics_prob = [(i,[(jj[0],float(jj[1])) for jj in j]) for i,j in document_topics[2]]
            per_word_topics_prob = {k : v for k, v in document_topics_prob}
            per_word_topics_prob = {dictionary[k] : v for k, v in document_topics_prob}
            # keep only what might be interesting to the user
            labeled = dict([(k, v) for k, v in item.items()] + 
                [("topics", topics),("per_word_topics_prob", per_word_topics_prob)])
            docs_complete.append(labeled)
    
    # Complete docs with extra topics+terms info     
    with gzip.open(args.output, "wt") as ofd:
        ofd.write(json.dumps(docs_complete))

