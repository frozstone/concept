from lxml import etree
from os import path
from unification import Unification
from pickle import load, dump
from multiprocessing import Pool
from sys import argv
import time

initial_address = argv[1]
target_address = argv[2]
query_address = argv[3]

def get_unicode(string):
    if type(string) is str:
        return string.decode("utf-8")
    else:
        return string

def extract_mathmlcontent_from_dataset(mt_xml):
    ann_xmls = mt_xml.xpath(".//annotation-xml[@encoding = 'MathML-Content']")
    if len(ann_xmls) > 0:
        return ann_xmls[-1]
    else:
        return None

#create query
#query_address = "NTCIR12-MathWiki-queries-participants.xml"
query_doc = etree.parse(query_address)
query_formulae = query_doc.xpath(".//*[local-name() = 'formula']")

queries = {}
for f in query_formulae:
    qid = f.getparent().getparent()[0].text
    
    if qid not in queries: queries[qid] = []
    ann_xmls = f.xpath(".//*[local-name() = 'annotation-xml' and @encoding = 'MathML-Content']")
    queries[qid].append(ann_xmls[-1])

#read the mathtext
mt_addresss = initial_address #"../../mcatsearch/submission_allfields_lr/math_text_dump_docs_all.dat"
mt = load(open(mt_addresss, "rb"))

source_root = "/data/private/giovanni/ntcir12-wiki/mathml/math_new/"
def get_math_repr(mid):
    para_path, kmcsid, latexmlid = mid.split("#")
    math_lns = open(path.join(source_root, para_path)).readlines()
    
    parafl = path.basename(para_path)
    for ln in math_lns:
        cells = ln.split("\t")
        if get_unicode(cells[0]) == get_unicode(latexmlid) and get_unicode(cells[1]) == get_unicode(parafl) and cells[2] == kmcsid: 
            return "\t".join(cells[3:])

def do_unification((mt_str_query, mt_str_dt)):
    mt_xml_query = etree.fromstring(mt_str_query)

    m_repr = get_math_repr(mt_str_dt)
    mt_xml_dt = etree.fromstring(m_repr)
    mt_xml_b = extract_mathmlcontent_from_dataset(mt_xml_dt)
    if mt_xml_b is None: return mt_str_dt, False
    mt_xml_b.tag = "semantics"

    u = Unification()
#    print etree.tostring(mt_xml_query)
#    print etree.tostring(mt_xml_b)
    matchlevel, isunify = u.align(mt_str_query, etree.tostring(mt_xml_b))
    return mt_str_dt, isunify

def do_unification_query(qid, dt):
#    try:
    start = time.time()
    math_lists = dt.values()[0]
    retval = []

    for list_i, math_units in enumerate(math_lists):
        retval.append({})

        mt_xml_a = queries[qid][list_i]
        mt_xml_a.tag = "semantics"
        mt_str_a = etree.tostring(mt_xml_a)

        #m_debug = "MathTagArticles/wpmath0000007/Articles/Baker_percentage.html#__MATH_6__#./Baker_percentage:6"
        #print do_unification((mt_str_a, m_debug))
        #print q
        data_to_parallel = [(mt_str_a, k) for k in math_units.keys()]
        p = Pool(processes = 50)
        for m, isunify in p.map(do_unification, data_to_parallel):
            score = math_units[m]
            retval[list_i][m] = 2*score if isunify else score
            #if m == m_debug: print m, isunify
    print qid, time.time() - start
    return retval
#    except:
#        print qid, "eror"

isunif = {}
for qid, dt in mt.iteritems():
#    qid = "NTCIR12-MathWiki-2"
    isunif[qid] = do_unification_query(qid, dt)

f = open(target_address, "wb")#"submission_allfields_lr/math_text_dump_docs_all.dat", "wb")
dump(isunif, f)
f.close()
