from collections                    import OrderedDict
from unification.unification_acl    import UnificationACL

import requests, json
import operator
import re
import solr

class Query_All:
    solr_connection = ''
    n_row = 0
    batchsize = 0
    __unifier = None

    def __init__(self, solrurl, nrow, batchsize=100):
        self.solr_connection = solr.SolrConnection(solrurl)
        self.n_row = nrow
        self.batchsize = batchsize
        self.__unifier = UnificationACL()

    def __escape(self, string):
        return re.sub(r'([+&|!(){}[\]"\'~*?:\\^-])', r'\\\1', string)

    #GENERATING A LIST OF RETR. UNIT
    
    def __ask_solr_math_max(self, response, mt_str_query):
        maths_score = []
        document_score = {}
        for doc in response.results:
            gmid = doc['gmid']
            gpid = doc.get("gpid")
            mml  = doc['mathml'].strip()
            gdoc = doc['gdoc']
            desc = doc['descriptions_xhtml'] if "descriptions_xhtml"  in doc else ""
            score = doc['score']

            try:
                isunify = self.__unifier.unify_string(mt_str_query, mml)
                if isunify: score = 2*score
            except:
                print "DEBUG: %s" % mt_str_query

            maths_score.append((gdoc, gmid, gpid, mml, desc, score))
            if gpid not in document_score or (gpid in document_score and score > document_score[gpid]):
                document_score[gpid] = score
        return maths_score, document_score

    def __ask_solr_mathunit_max(self, response):
        maths_score = {}
        document_score = {}
        while True:
            for doc in response.results:
                gmid = doc['gmid']
                gdoc = doc['gdoc']
                score = doc['score']
                maths_score[gmid] = score
                if (gdoc not in document_score) or (gdoc in document_score and score > document_score[gdoc]):
                    document_score[gdoc] = score
            response = response.next_batch()
            if not response or len(maths_score) >= self.n_row: break
        return maths_score, document_score


    def __ask_solr_docdb_max(self, response):
        document_score = {}
        while True:
            for doc in response.results: 
                gdoc = doc["gdoc"]
                score = doc["score"]
                document_score[gdoc] = score
            response = response.next_batch()
            if not response or len(document_score) >= self.n_row: break
        return document_score

    #CONSTRUCT A SOLR QUERY
    def __ask_solr_math(self, query, mt_str_query):
        resp = self.solr_connection.query(q = query, fields = ("*, score"), rows = self.n_row)
        return self.__ask_solr_math_max(resp, mt_str_query)

    def __ask_solr_docdb(self, query):
        resp = self.solr_connection.query(q = query, fields = ("gdoc, score"), rows = self.n_row)
        return self.__ask_solr_docdb_max(resp)

    def ask_solr_math_score(self, query, gmid):
        resp = self.solr_connection.query(q = query, fields = ("score"), fq = "gmid:(%s)" % gmid)
        return resp.results[0]['score'] if len(resp.results) > 0 else 0.0

    def ask_solr_max_score(self, query):
        resp = self.solr_connection.query(q = query, fields = ('score'))
        return resp.maxScore

    #INTERFACING WITH OUTSIDE WORLD

    def __produce_fquery(self, queries):
        fquery = "{!func}"
        list_localparams = []
        for wgt, q in queries:
            querystring = "{!type=lucene v='%s'}" % self.__escape(q)
            list_localparams.append("product(%s, div(1, sum(1, div(1,query(%s)))))" % (wgt, querystring))
        localparams = "%ssum(%s)" % (fquery, ",".join(list_localparams))
        return localparams

    def __produce_fquery_wo_weight(self, queries):
        fquery = "{!func}"
        list_localparams = []
        for q in queries:
            querystring = "{!type=lucene v='%s'}" % self.__escape(q)
            list_localparams.append("div(1, sum(1, div(1,query(%s))))" % querystring)
        localparams = "%ssum(%s)" % (fquery, ",".join(list_localparams))
        return localparams

    def __produce_commonquery(self, queries):
        query_fields = [q for q in queries]
        common_query = " ".join(query_fields)
        return common_query

    def ask_solr_math_fqueries(self, query, mt_str_query):
        fquery = self.__produce_fquery_wo_weight(query)
        #fquery = self.__produce_fquery(query)
        #fquery = self.__produce_commonquery(query)
        maths, documents = self.__ask_solr_math(fquery, mt_str_query)
        documents = sorted(documents.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.n_row]
        return maths, documents

    def ask_solr_doc_fqueries(self, query):
        fquery = self.__produce_fquery_wo_weight(query)
        #fquery = self.__produce_fquery(query)
        #fquery = self.__produce_commonquery(query)
        documents = self.__ask_solr_docdb(fquery)
        documents = sorted(documents.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.n_row]
        return documents

