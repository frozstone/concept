from nltk.tokenize  import word_tokenize
from nltk.stem      import PorterStemmer
import math 
import solr

class WordSim:
    __top_size = 5
    __solr_connection = None
    __unique_terms = 3529371
    __stop_words = set()
    __stemmer = None

    def __init__(self, solrurl):
        self.__solr_connection = solr.SolrConnection(solrurl)
        self.__stemmer = PorterStemmer()
        for ln in open("resources/SmartStoplist.txt").readlines()[1:]:
            if ln.strip() != "": self.__stop_words.add(ln.strip())

    def __ask_solr_n_count(self, query):
        resp = self.__solr_connection.query(q = query)
        return int(resp.numFound)

    def __n_count(self, *arg):
        query_solr = " AND ".join(['body:"%s"' % a for a in arg])
        return self.__ask_solr_n_count(query_solr)

    def __dice_word(self, w1, w2):
        p1p2 = self.__n_count(w1, w2)
        p1   = self.__n_count(w1)
        p2   = self.__n_count(w2)
        return (1.0*self.__unique_terms*p1p2) / (1+p1+p2)

    def __pmi_word(self, w1, w2):
        p1p2 = self.__n_count(w1, w2)
        p1   = self.__n_count(w1)
        p2   = self.__n_count(w2)
        return math.log(1 + (1.0*self.__unique_terms*p1p2) / (1+p1*p2))

    def __dice_term(self, t1, t2):
        scores = []
        words1 = word_tokenize(t1)
        words2 = word_tokenize(t2)
        for w1 in words1:
            for w2 in words2:
                scores.append(self.__dice_word(w1, w2))
        scores.sort(reverse=True)
        topscores = scores[:max(len(words1), len(words2))]
        return sum(topscores)

    def __pmi_term(self, t1, t2):
        scores = []
        words1 = [w for w in word_tokenize(t1) if w not in self.__stop_words and w.isalnum()]
        words2 = [w for w in word_tokenize(t2) if w not in self.__stop_words and w.isalnum()]
        for w1 in words1:
            for w2 in words2:
                sc = self.__pmi_word(w1, w2)
                scores.append(self.__pmi_word(w1, w2))
        scores.sort(reverse=True)
        topscores = scores[:max(len(words1), len(words2))]
        return sum(topscores)

    def __jaccard_term(self, t1, t2):
        t1 = t1.lower()
        t2 = t2.lower()
        words1 = [self.__stemmer.stem(w) for w in word_tokenize(t1) if w not in self.__stop_words and self.__stemmer.stem(w) not in self.__stop_words and w.isalnum()]
        words2 = [self.__stemmer.stem(w) for w in word_tokenize(t2) if w not in self.__stop_words and self.__stemmer.stem(w) not in self.__stop_words and w.isalnum()]

        words_1and2 = set(words1).intersection(set(words2))
        words_1or2  = set(words1).union(set(words2))

        if len(words_1or2) == 0: return 0
        return (1.0 * len(words_1and2)) / len(words_1or2)

    def dice(self, texts1, texts2):
        return self.__dice_term(" ".join(texts1), " ".join(texts2))
        
    def pmi(self, texts1, texts2):
        return self.__pmi_term(" ".join(texts1), " ".join(texts2))

    def jaccard(self, texts1, texts2):
        return self.__jaccard_term(" ".join(texts1), " ".join(texts2))
