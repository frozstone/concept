from nltk.parse.stanford    import StanfordParser
from nltk.stem.porter       import PorterStemmer
from nltk.tokenize          import sent_tokenize, word_tokenize
import math

class SentenceParser:
    __parser = None
    __alpha  = 1.0
    __beta   = 1.0
    __gamma  = 0.1

    __var_d  = 0.0
    __var_s  = 0.0

    def __init__(self):
        self.__parser = StanfordParser()
        self.__var_d  = 12.0/math.log(2.0)
        self.__var_s  = 4.0 * 1.0/math.log(2)

    def __parse_sent(self, sentence):
        result = self.__parser.raw_parse(sentence) 
        return result.next()

    def __obtain_nps(self, sentence):
        parse_tree = self.__parse_sent(sentence)
        nps = set()
        for phrase in parse_tree.subtrees():
            if phrase.label() != "NP": continue
            nps.add(' '.join(phrase.leaves()))

        sent_tokens = " ".join(parse_tree.leaves())
        
        #Get the smallest NPs
        nps_smallest = set()
        for np1 in nps:
            if all(np2 not in np1 for np2 in nps if np2 != np1): 
                nps_smallest.add(np1)
        return sent_tokens, nps_smallest

    def __gaussian_weight(self, distance, variance):
        return math.exp(-0.5 * (distance**2 - 1)/variance)

    def __weight_tokens(self, mid, nps, sentences, sent_id):
        st          = PorterStemmer()
        sent_target = sentences[sent_id]
        token_id    = [idx for idx, token in enumerate(sent_target.strip().split(" ")) if mid in token][0]

        sent_lengths= [len(s.split(" ")) for s in sentences]

        nps_base = {np:" ".join(st.stem(token) for token in np.split(" ")) for np in nps}
        nps_proc = {}

        for sent_idx, sent in enumerate(sentences):
            sent_stem = " ".join(st.stem(token) for token in sent.split(" "))
            for np_ori, np in nps_base.iteritems():
                if np_ori not in nps_proc: nps_proc[np_ori] = {}

                if "dist_sent" not in nps_proc[np_ori] or abs(sent_idx - sent_id) < nps_proc[np_ori]["dist_sent"]:
                    #always update the info
                    if np not in sent_stem: 
                        continue
                    np_idx      = sent_stem.rindex(np)
                    np_token_idx= len(sent_target[:np_idx].strip().split(" "))
                    dist_start  = len(sent_stem[:np_idx].strip().split(" "))
                    dist_end    = len(sent_stem[np_idx+len(np):].strip().split(" "))

                    dist_sent   = abs(sent_idx - sent_id)
                    dist_token  = -1

                    if dist_sent == 0:
                        if mid in np_ori:
                            dist_token = 0
                        elif np_token_idx < token_id:
                            dist_token = token_id - np_token_idx - (len(np.split(" ")) - 1) - 1
                        elif np_token_idx > token_id:
                            dist_token = np_token_idx - token_id - 1
                    elif sent_idx < sent_id: 
                        dist_token = dist_end + sum(sent_lengths[sent_idx+1:sent_id]) + token_id
                    elif sent_idx > sent_id:
                        dist_token = (len(sent_target.strip().split(" "))-1-token_id) + sum(sent_lengths[sent_id+1:sent_idx]) + dist_start

                    nps_proc[np_ori]["dist_sent"]  = dist_sent
                    nps_proc[np_ori]["dist_token"] = dist_token

                np_count = sent_stem.count(np)
                nps_proc[np_ori]["tf"] = (nps_proc[np_ori].get("tf") or 0) + np_count

        nps_weight = {}
        for np, vals in nps_proc.iteritems():
            term1 = self.__alpha * self.__gaussian_weight(vals["dist_token"], self.__var_d)
            term2 = self.__beta  * self.__gaussian_weight(vals["dist_sent"],  self.__var_s)
            term3 = self.__gamma * vals["tf"]
            nps_weight[np] = (term1 + term2 + term3) / (self.__alpha + self.__beta + self.__gamma)
        return nps_weight

    def obtain_nps_from_sentences(self, mid, text):
        lst_sentences = sent_tokenize(text)
        lst_sent_pr  = []
        set_nps      = set()

        sent_match_id= -1
        for sent_idx, sent in enumerate(lst_sentences):
            if sent_match_id == -1 and mid in sent: 
                sent_match_id = sent_idx

            sent_tokens, nps = self.__obtain_nps(sent)
            lst_sent_pr.append(sent_tokens)
            set_nps.update(nps)

        dct_nps_weight = self.__weight_tokens(mid, set_nps, lst_sent_pr, sent_match_id)
        return lst_sent_pr, dct_nps_weight

