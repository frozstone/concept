from nltk.parse.stanford    import StanfordParser
from nltk.tokenize          import sent_tokenize
class SentenceParser:
    __parser = None
    
    def __init__(self):
        self.__parser = StanfordParser()

    def __parse_sent(self, sentence):
        result = self.__parser.raw_parse(sentence) 
        return result.next()

    def __obtain_nps(self, sentence):
        parse_tree = self.__parse_sent(sentence)
        nps = set()
        for phrase in parse_tree.subtrees():
            if phrase.label() != "NP": continue
            nps.add(' '.join(phrase.leaves()))
        
        #Get the smallest NPs
        nps_smallest = set()
        for np1 in nps:
            if all(np2 not in np1 for np2 in nps if np2 != np1): 
                nps_smallest.add(np1)
        return nps_smallest

    def obtain_nps_from_sentences(self, text):
        lst_sentences = sent_tokenize(text)
        lst_nps      = []

        for sent in lst_sentences:
            lst_nps.append(self.__obtain_nps(sent))
                
        return lst_sentences, lst_nps

