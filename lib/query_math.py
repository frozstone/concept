from mathml_presentation_query import MathMLPresentation
from mathml_content_query import MathMLContent
from query_all import Query_All
import modular, sigure, subtree
from collections import OrderedDict
import functools
import operator
import re
from lxml import etree 
from MathConverter import MathConverter

re_escape = r'([+&|!(){}[\]"~*?:\\^-])'
re_qvar = r'\bqvar\b'

class Query:
    solr_url_math = ''
    n_row = 0
    
    def __init__(self, solrurlmath, nrow):
        self.solr_url_math = solrurlmath
        self.n_row = nrow

    def __escape(self, string):
        retval = ' '.join([token for token in re.sub(re_escape, r'\\\1', string).split(' ') if 'qvar' not in token])
        if retval.strip() == "":
            return '""'
        return retval

    def __getUnicodeText(self, string):
        if type(string) is str:
            return string.decode('utf-8')
        else:
            return string

    def get_op_arg_unif(self, paths):
        ops = []
        ops_unif = []
        args = []
        for p in paths:
            elem = p.split()
            op = ""
            op_unif = ""
            arg = ""
            for el in elem:
                if el.startswith("mo#") or "#mo#" in el:
                    op = ("%s %s" % (op, el)).strip()
                    op_unif = ("%s %s" % (op_unif, el)).strip()
                    continue
                if el.startswith("mi#") or "#mi#" in el or el.startswith("mn#") or "#mn#" in el:
                    arg = ("%s %s" % (arg, el)).strip()
                    cells = el.split("#")
                    if cells[-2] == "mi":
                        unif_concat = "#".join(cells[:-1])
                        op_unif = ("%s %s" % (op_unif, unif_concat)).strip()
                    continue
                op = ("%s %s" % (op, el)).strip()
                op_unif = ("%s %s"  % (op_unif, el)).strip()
                arg= ("%s %s" % (arg, el)).strip()
            if op.strip() != "": ops.append(op)
            if op_unif.strip() != "": ops_unif.append(op_unif)
            if arg.strip() != "": args.append(arg)
        return ops, ops_unif, args

    def __encodeMaths_path_pres(self, mts_string):
        procPres = MathMLPresentation('http://localhost:9000/upconvert')
        semantics, mathml_string, mathml_presentation = procPres.get_doc_with_orig(mts_string)
        opaths = []
        opaths_ops = []
        opaths_args = []
        upaths = []
        upaths_ops = []
        upaths_args = []
        sisters = []
        if semantics is not None:
            opaths, sisters = procPres.get_ordered_paths_and_sisters(semantics, False)
            upaths = map(lambda paths: ' '.join(map(self.__getUnicodeText, paths)), procPres.get_unordered_paths(opaths))
            opaths = map(lambda paths: ' '.join(map(self.__getUnicodeText, paths)), opaths)
            opaths_ops, opaths_ops_unif, opaths_args = self.get_op_arg_unif(opaths)
            upaths_ops, upaths_ops_unif, upaths_args = self.get_op_arg_unif(upaths)
        return opaths_ops, opaths_args, upaths_ops, upaths_args, sisters

    def __encodeMaths_hash_pres(self, mts_string):
        procPres = MathMLPresentation('http://localhost:9000/upconvert')
        semantics, mathml_string, mathml_presentation = procPres.get_doc_with_orig(mts_string)
        psubhash = []
        psighash = []
        pmodhash = []
        if semantics is not None:
            psubhash = subtree.hash_string(mathml_presentation)
            psighash = sigure.hash_string(mathml_presentation)
            pmodhash = modular.hash_string_generator(2 ** 32)(mathml_presentation)
        return psubhash, psighash, pmodhash

    def __constructSolrQuery_math_path_pres(self, qmath):
        opath_ops, opath_args, upath_ops, upath_args, sister = self.__encodeMaths_path_pres(qmath)
#        opath_query = "opaths:(%s)" % self.__escape(' '.join(opath))
#        upath_query = "upaths:(%s)" % self.__escape(' '.join(upath))
        opath_ops_query = "p_opaths_op:(%s)" % (self.__escape(opath_ops[0]) if len(opath_ops) > 0 else '""')
        opath_arg_query = "p_opaths_arg:(%s)" % (self.__escape(opath_args[0]) if len(opath_args) > 0 else '""')

        upath_ops_query = "p_upaths_op:(%s)" % (self.__escape(upath_ops[0]) if len(upath_ops) > 0 else '""')
        upath_arg_query = "p_upaths_arg:(%s)" % (self.__escape(upath_args[0]) if len(upath_args) > 0 else '""')

        sister = [s for s in sister if ''.join(s).replace('qvar', '').strip() != '']
        sister_query = ' '.join(map(lambda family: 'p_sisters:("%s")' % self.__escape(' '.join(family)), sister))
        return opath_ops_query, opath_arg_query, upath_ops_query, upath_arg_query, sister_query

    def __constructSolrQuery_math_hash_pres(self, qmath):
        psubhash, psighash, pmodhash = self.__encodeMaths_hash_pres(qmath)
        psubhash_query = "p_stree_hashes:(%s)" % (' '.join([str(val) for val in psubhash]).replace('-', '\-') if len(psubhash) > 0 else '*')
        psighash_query = "p_sigure_hashes:(%s)" % (' '.join([str(val) for val in psighash]).replace('-', '\-') if len(psighash) > 0 else '*')
        pmodhash_query = "p_mtrick_hashes:(%s)" % (' '.join([str(val) for val in pmodhash]).replace('-', '\-') if len(pmodhash) > 0 else '*')
        return psubhash_query, psighash_query, pmodhash_query


    def __constructSolrQuery_math_pres(self, query_element):
        #construct math query
        query_op_opath = ''
        query_arg_opath = ''
        query_op_upath = ''
        query_arg_upath = ''
        query_sister = ''

        query_psubhash = ""
        query_psighash = ""
        query_pmodhash = ""

        opath_op_query, opath_arg_query, upath_op_query, upath_arg_query, sister_query = self.__constructSolrQuery_math_path_pres(query_element)
        psubhash_query, psighash_query, pmodhash_query = self.__constructSolrQuery_math_hash_pres(query_element)

        #comb:path pres
        query_op_opath = ' '.join([query_op_opath, opath_op_query]).strip()
        query_arg_opath = ' '.join([query_arg_opath, opath_arg_query]).strip()

        query_op_upath = ' '.join([query_op_upath, upath_op_query]).strip()
        query_arg_upath = ' '.join([query_arg_upath, upath_arg_query]).strip()

        query_sister =  ' '.join([query_sister, sister_query]).strip()

        #comb3: hash pres
        query_psubhash = " ".join([query_psubhash, psubhash_query]).strip()
        query_psighash = " ".join([query_psighash, psighash_query]).strip()
        query_pmodhash = " ".join([query_pmodhash, pmodhash_query]).strip()

        return query_op_opath, query_arg_opath, query_op_upath, query_arg_upath, query_sister, query_psubhash, query_psighash, query_pmodhash


    def __encodeMaths_path_cont(self, mts_string):
        procCont = MathMLContent()
        oopers = []
        oargs = []
        uopers = []
        uargs = []
        trees, cmathmls_str = procCont.encode_mathml_as_tree(mts_string)
        for tree in trees:
            ooper, oarg = procCont.encode_paths(tree)
            uoper = procCont.get_unordered_paths(ooper)
            uarg = procCont.get_unordered_paths(oarg)
            oopers.extend(map(self.__getUnicodeText, ooper))
            uopers.extend(map(self.__getUnicodeText, uoper))
            oargs.extend(map(self.__getUnicodeText, oarg))
            uargs.extend(map(self.__getUnicodeText, uarg))
#        oopers = map(lambda paths: ' '.join(paths), oopers)
#        oargs = map(lambda paths: ' '.join(paths), oargs)
#        uopers = map(lambda paths: ' '.join(paths), uopers)
#        uargs = map(lambda paths: ' '.join(paths), uargs)
#        return oopers, oargs, uopers, uargs
        return oopers[-1], oargs[-1], uopers[-1], uargs[-1]

    def __encodeMaths_hash_cont(self, mts_string):
        procCont = MathMLContent()
        trees, cmathmls_str = procCont.encode_mathml_as_tree(mts_string)
        csubhash = []
        csighash = []
        cmodhash = []
        for cmathml_str in cmathmls_str:
            csubhash.extend(subtree.hash_string(cmathml_str))
            csighash.extend(sigure.hash_string(cmathml_str))
            cmodhash.extend(modular.hash_string_generator(2 ** 32)(cmathml_str))
        return csubhash, csighash, cmodhash

    def __constructSolrQuery_math_path_cont(self, qmath):
        ooper, oarg, uoper, uarg = self.__encodeMaths_path_cont(qmath)
        ooper_query = "c_opaths_op:(%s)" % self.__escape(' '.join(ooper))
        oarg_query = "c_opaths_arg:(%s)" % self.__escape(' '.join(oarg))
        uoper_query = "c_upaths_op:(%s)" % self.__escape(' '.join(uoper))
        uarg_query = "c_upaths_arg:(%s)" % self.__escape(' '.join(uarg)) 
        return ooper_query, oarg_query, uoper_query, uarg_query

    def __constructSolrQuery_math_hash_cont(self, qmath):
        csubhash, csighash, cmodhash = self.__encodeMaths_hash_cont(qmath)
        csubhash_query = "c_stree_hashes:(%s)" % (' '.join([str(val) for val in csubhash]).replace('-', '\-') if len(csubhash) > 0 else '*')
        csighash_query = "c_sigure_hashes:(%s)" % (' '.join([str(val) for val in csighash]).replace('-', '\-') if len(csighash) > 0 else '*')
        cmodhash_query = "c_mtrick_hashes:(%s)" % (' '.join([str(val) for val in cmodhash]).replace('-', '\-') if len(cmodhash) > 0 else '*')
        return csubhash_query, csighash_query, cmodhash_query
        

    def __constructSolrQuery_math_cont(self, query_element):
        #construct math query
        query_ooper = ""
        query_oarg = ""
        query_uoper = ""
        query_uarg = ""

        query_csubhash = ""
        query_csighash = ""
        query_cmodhash = ""

        ooper_query, oarg_query, uoper_query, uarg_query = self.__constructSolrQuery_math_path_cont(query_element)
        csubhash_query, csighash_query, cmodhash_query = self.__constructSolrQuery_math_hash_cont(query_element)
        
        #comb2: path content
        query_ooper = " ".join([query_ooper, ooper_query]).strip()
        query_oarg = " ".join([query_oarg, oarg_query]).strip()
        query_uoper = " ".join([query_uoper, uoper_query]).strip()
        query_uarg = " ".join([query_uarg, uarg_query]).strip()

        #comb4: hash content
        query_csubhash = " ".join([query_csubhash, csubhash_query]).strip()
        query_csighash = " ".join([query_csighash, csighash_query]).strip()
        query_cmodhash = " ".join([query_cmodhash, cmodhash_query]).strip()

        return query_ooper, query_oarg, query_uoper, query_uarg, query_csubhash, query_csighash, query_cmodhash

    def __constructSolrQuery_words(self, keywords):
        text_fields = []
        or_terms    = ' OR '.join('"%s"^%s' % (term, term_weight) for term, term_weight in keywords.iteritems())
        for fld in ["contexts", "contexts_children", "nounphrases", "nounphrases_children", "descriptions", "descriptions_children"]:
            text_fields.append("%s:(%s)" % (fld, or_terms))
        return text_fields 

    def __summarize_score_max(self, all_maths):
        return max(all_maths.values()) 

    def askSolr_all_pres(self, query):
        qall = Query_All(self.solr_url_math, self.n_row)

        fields = []
        if query["mathml"] != "":
            mc = MathConverter()
            mathml = query['mathml']
            terms_fields = self.__constructSolrQuery_math_pres(mathml)
            fields += list(terms_fields)
        
        if len(query["text"]) > 0: #query['text'].strip() != "":
            text_fields = self.__constructSolrQuery_words(query['text'])
            fields += text_fields
        qmath, qdocs = qall.ask_solr_math_fqueries(fields, query["mathml"])
        return qmath, qdocs
  
