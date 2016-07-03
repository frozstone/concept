from query_all import Query_All
import modular, sigure, subtree
from collections import OrderedDict
import functools
import operator
import re

re_escape = r'([+&|!(){}[\]"~*?:\\^-])'
re_qvar = r'\bqvar\b'

class Query:
    solr_url_math = ''
    n_row = 0

    def __init__(self, solrurlmath, nrow):
        self.solr_url_math = solrurlmath
        self.n_row = nrow

    def __escape(self, string):
        return ' '.join([token for token in re.sub(re_escape, r'\\\1', string).split(' ') if 'qvar' not in token]) 

    def __getUnicodeText(self, string):
        if type(string) is str:
            return string.decode('utf-8')
        else:
            return string

    def __constructSolrQuery_words_verbose(self, query_element):
        #construct keyword query
        terms_word          = ' OR '.join('"%s"^%s' % (term, term_weight) for term, term_weight in query_element["keyword"].iteritems())
        abstract_query      = 'abstract:(%s)' % terms_word
        body_query          = 'body:(%s)' % terms_word
        descriptions_query  = 'descriptions:(%s)' % terms_word
        keywords_query      = 'keywords:(%s)' % terms_word
        nounphrases_query   = 'nounphrases:(%s)' % terms_word
        title_query         = 'title:(%s)' % terms_word

        term_query          = 'term:(%s)' % terms_word
        innerlink_query     = 'innerlink:(%s)' % terms_word
        subject_query       = 'subject:(%s)' % terms_word
        return abstract_query, body_query, descriptions_query, keywords_query, nounphrases_query, title_query, term_query, innerlink_query, subject_query

    def __summarize_score_max(self, all_maths):
        return max(all_maths.values()) 

    def askSolr_all_verbose(self, query):
        if len(query["keyword"]) == 0: return {}
        qall = Query_All(self.solr_url_math, self.n_row)
        a, b, d, k, n, t , tm, inl, subj = self.__constructSolrQuery_words_verbose(query)

        queries = [a,b,d,k,n,t, tm, inl, subj]

        qdocs = qall.ask_solr_doc_fqueries(queries)
        return qdocs
