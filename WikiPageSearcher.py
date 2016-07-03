import lib.query_math as qm
import lib.query_doc  as qd
from nltk import word_tokenize
from nltk.corpus import stopwords
from lxml import etree


class WikiPageSearcher:
    __solr_math_url  = None
    __solr_doc_url   = None
    __seed_size = 100
    __stops     = None

    def __init__(self, solr_math_url, solr_doc_url):
        self.__solr_math_url = solr_math_url
        self.__solr_doc_url  = solr_doc_url
        self.__stops = set(stopwords.words("english"))

    def __remove_stops(self, text):
        newtext = []
        for token in word_tokenize(text):
            if token.lower() not in self.__stops: newtext.append(token)
        return " ".join(newtext)

    def __rename_gdoc(self, gdoc):
        wpage = gdoc.split("/")[-1]
        return wpage.replace(".html", "")

    def __search_wikipedia_mathdb(self, mathml, text):
        """
            mathml: string
        """
        q = qm.Query(self.__solr_math_url, self.__seed_size)

        #query = {'mathml': mathml, 'text': self.__remove_stops(text)}
        query = {'mathml': mathml, 'text': text}

        qmath, _ = q.askSolr_all_pres(query)
        
        topdocs = set()
        topdocs_and_score = []
        for gdoc, gmid, gpid, mml, desc, score in qmath:
            gdoc_simple = self.__rename_gdoc(gdoc)

            if gdoc_simple in topdocs: continue
            topdocs_and_score.append((gdoc_simple, score))
            topdocs.add(gdoc_simple)
        return topdocs_and_score

    def __search_wikipedia_docdb(self, text):
        q = qd.Query(self.__solr_doc_url, self.__seed_size)

        #query   = {'keyword': self.__remove_stops(text)}
        query   = {'keyword': text}

        qdoc    = q.askSolr_all_verbose(query)

        topdocs_and_score = []
        for gdoc, score in qdoc:
            gdoc_simple = self.__rename_gdoc(gdoc)
            topdocs_and_score.append((gdoc_simple, score))
        return topdocs_and_score

    def search_wikipedia_pages(self, mathml, text):
        """
            mathml: string
            text: dictionary of nps and their weights
        """
        result_mathdb = self.__search_wikipedia_mathdb(mathml, text)
        result_docdb  = self.__search_wikipedia_docdb(text)
        return result_mathdb, result_docdb
