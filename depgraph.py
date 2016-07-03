#!/usr/local/bin/python

from AnnReader          import AnnReader
from MathReader         import MathReader
#from Cluster            import Cluster
from DepGraphProcessor  import DepGraphProcessor
from HeurDep            import HeurDep
from ParaReader         import ParaReader
from SentenceParser     import SentenceParser
from WikiPageSearcher   import WikiPageSearcher
from WordSim            import WordSim

from utilities.norm_attribute   import norm_attribute
from utilities.utils            import Link_Types, Matching_Methods

from collections        import OrderedDict
from lxml               import etree
from os                 import path, listdir
from pickle             import load, dump
from sys                import argv
import numpy as np

#Properties
xml_dir         = "../ACL-ARC-math-20"
ann_dir         = "../bios_long"
solr_wiki_pmi   = "http://localhost:8983/solr/wiki.document"
solr_wiki_math  = "http://localhost:8983/solr/mcatwiki.math"
solr_wiki_doc   = "http://localhost:8984/solr/conceptwiki.document"

def set_data(math_knowledge):
    word_sim = WordSim(solr_wiki_pmi)
    nodes   = set([])
    labels  = {}
    
    for mid in math_knowledge.keys():
        idx = int(mid[mid.rindex("_")+1:])
        nodes.add(idx)
        labels[idx] = str(idx)

    edges = np.zeros(shape=(max(nodes)+1, max(nodes)+1))
    for mid1, knowledge1 in math_knowledge.iteritems():
        idx1 = int(mid1[mid1.rindex("_")+1:])

        #get score for description similarity
        for mid2, knowledge2 in math_knowledge.iteritems():
            idx2 = int(mid2[mid2.rindex("_")+1:])
            #pmi  = word_sim.pmi(knowledge1["descriptions"], knowledge2["descriptions"])
            #pmi  = max(0,pmi/(10+pmi))
            #edges[idx1, idx2] += pmi

            #sim   = word_sim.jaccard(knowledge1["descriptions"], knowledge2["descriptions"])
            #edges[idx1, idx2] += sim

        if "children" not in knowledge1: continue
        for ch in knowledge1["children"]:
            idx_ch = ch[0]
            idx_ch = int(idx_ch[idx_ch.rindex("_")+1:])
            if ch[1] is Link_Types.comp or ch[1] is Link_Types.simcomp:
                edges[idx1,idx_ch]  += 1
                edges[idx_ch, idx1] += 1
            if ch[1] is Link_Types.exp or ch[1] is Link_Types.simexp:
                edges[idx1,idx_ch]  += 1
                #edges[idx_ch, idx1] += 1

    edges = np.matrix(edges)
    return nodes, labels, edges

def encode(text):
    if type(text) is unicode: return text.encode("utf-8")
    return text

def print_dict(d):
    for k, v in d.iteritems():
        print k, etree.tostring(v)

def print_nodes(d, math_map):
    nodes = sorted(d, key = lambda dt: int(dt[dt.rindex("_")+1:]))
    for n in nodes:
        print n, etree.tostring(math_map[n])

def print_docs_score(docs_score):
    lst_string = ["(%s, %f)" % (encode(doc), score) for doc, score in docs_score]
    return ", ".join(lst_string)

def nps_aggregration(lst_dct_weighted_nps):
    agg_nps = {}
    for nps in lst_dct_weighted_nps:
        for np, weight in nps:
            if np not in agg_nps: agg_nps[np] = 0.0
            agg_nps[np] += weight

    agg_agv_nps = {np:sum_weight/len(lst_dct_weighted_nps) for np, sum_weight in agg_nps.iteritems()}
    return agg_agv_nps

def search_wiki(math_knowledge, math_map, mcom_map, roots, math_exp_rev, old_new_math_map):
    ws = WikiPageSearcher(solr_wiki_math, solr_wiki_doc)
    na = norm_attribute()
    for mid, vals in math_knowledge.iteritems():
        mml = etree.tostring(math_map[mid])
        mml = na.normalize(mml)

        mml_comp = etree.tostring(mcom_map[mid])
        mml_comp = na.normalize(mml_comp)
        
        lst_dct_weighted_nps = []
        lst_dct_weighted_nps.append(vals["nps"])

        if "children" in vals:
            for v, vt in vals["children"]:
                if vt is Link_Types.comp or vt is Link_Types.simcomp: continue
                #text = u"%s %s" % (text, math_knowledge[v]["paragraph"])
                lst_dct_weighted_nps.append(math_knowledge[v]["nps"])

        agg_nps = nps_aggregration(lst_dct_weighted_nps)
        mathdb, docdb = ws.search_wikipedia_pages(mml_comp, agg_nps)
        
        is_root = old_new_math_map[math_exp_rev[mid]] in roots
        is_root = str(is_root)

        mml_to_print = etree.fromstring(etree.tostring(math_map[mid]))
        etree.strip_tags(mml_to_print, "*")
        print "\t".join((is_root, mid, encode(mml_to_print.text), print_docs_score(mathdb), print_docs_score(docdb)))

def maincode(fl, mode_dump):
    ann_reader  = AnnReader()
    #cluster     = Cluster()
    dep_getter  = HeurDep()
    math_reader = MathReader()
    para_reader = ParaReader(path.join(xml_dir, fl))
    sent_parser = SentenceParser()

    pname = fl.split("_")[0]

    math_map = math_reader.read_maths(xml_dir, pname)
    mcom_map = math_reader.read_complete_maths(xml_dir, pname)
    desc_map = ann_reader.get_paper_ann(ann_dir, pname)
    depgraph = dep_getter.get_dep_graph(math_map, Matching_Methods.heur)
    para_map = OrderedDict()
    sent_map = OrderedDict()
    nps_map  = OrderedDict()
    for mid, xmml in math_map.iteritems():
        infty_mid       = xmml.attrib["id"]
        para_text       = para_reader.get_paragraph_for_math(infty_mid)
        para_map[mid]   = para_text
        
        sents, nps      = sent_parser.obtain_nps_from_sentences(mid, para_text) 
        sent_map[mid]   = sents
        nps_map[mid]    = nps

    #Compressing/Simplifying dep graph
    dep_proc        = DepGraphProcessor(math_map, desc_map, para_map, depgraph)
    (math_map_new, desc_map_new, para_map_new, depgraph_new, old_new_math_map), math_exp_rev = dep_proc.compress_depgraph()

    roots           = dep_proc.get_roots(math_map_new, depgraph_new)
    sink_nodes      = dep_proc.get_sink_nodes(math_map_new, depgraph_new)

    #if mode_dump == "1": print_nodes(roots, math_map_new)
    #if mode_dump == "2": print_nodes(sink_nodes, math_map_new)


    #Processing without node compression
    math_knowledge = OrderedDict.fromkeys(math_map.keys())
    math_ids = set(depgraph.keys()).union(set(desc_map.keys())).union(set(math_map.keys()))

    for mid in math_ids:
        math_knowledge[mid] = {}
        math_knowledge[mid]["descriptions"] = desc_map[mid] if mid in desc_map else []
        math_knowledge[mid]["paragraph"]    = para_map[mid]
        math_knowledge[mid]["nps"]          = nps_map[mid]
        if mid in depgraph:
            math_knowledge[mid]["children"] = depgraph[mid]

    #FIND the wiki article related to the roots
    search_wiki(math_knowledge, math_map, mcom_map, roots, math_exp_rev, old_new_math_map)

    #data = set_data(math_knowledge)
    #nodes, labels, edges = data
    #cluster.comm_detect(labels, edges, math_map, desc_map)



if __name__ == "__main__":
    fl          = argv[1]
    mode_dump   = argv[2]

#    try:
    maincode(fl, mode_dump)
#    except:
#        print fl
