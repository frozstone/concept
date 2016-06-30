from os import listdir, path
from lxml import etree, objectify
from pickle import load
from sys import argv
from StringIO import StringIO
from collections import OrderedDict
import time

from utilities.norm_arxiv       import norm_arxiv
from utilities.norm_attribute   import norm_attribute
from utilities.norm_mrow        import norm_mrow
from utilities.norm_outer_fence import norm_outer_fence
from utilities.norm_splitter    import norm_splitter
from utilities.norm_tag         import norm_tag

from utilities.utils            import Link_Types, Matching_Methods, utils
from utilities.depgraph_heur    import depgraph_heur

class HeurDep:
    __dtd = '<!DOCTYPE math SYSTEM "resources/xhtml-math11-f.dtd">'
    __xmlns = ' xmlns="http://www.w3.org/1998/Math/MathML"'
    __relation_fl = 'resources/math_symbols_unicode.dump'
    __xml_parser = etree.XMLParser(remove_blank_text = True, load_dtd = True, resolve_entities = True)


    def __get_clean_mathml(self, mt_string):
        mt_tree = etree.parse(StringIO(self.__dtd + mt_string), self.__xml_parser).getroot()
        objectify.deannotate(mt_tree, cleanup_namespaces=True)
        return mt_tree

    def __extract_math_line_arxiv(self, line):
        cells = line.strip().split('\t')
        latexml_id  = cells[0]
        para_id     = cells[1]
        kmcs_id     = cells[2]
        gmid        = '#'.join([para_id, kmcs_id, latexml_id])

        mt_string = '\t'.join(cells[3:]).replace(self.__xmlns, "")
        mt = self.__get_clean_mathml(mt_string)
        return gmid, mt

    def __extract_math_line_acl(self, line):
        cells = line.strip().split('\t')
        gmid  = cells[0]

        mt_string = '\t'.join(cells[1:]).replace(self.__xmlns, "")
        mt = self.__get_clean_mathml(mt_string)
        return gmid, mt

    def get_dep_graph(self, maths, matching_method):
        '''
        input: file from math_new
        output: 
            1. edges: {gumid1:[(gumid2, linktype)]} --> component list
            2. gumidmappings: {gmid:gumid}
        '''
        #useful utilities classes
        n_arxiv         = norm_arxiv()
        n_attribute     = norm_attribute()
        n_mrow          = norm_mrow(self.__dtd)
        n_outer_fence   = norm_outer_fence()
        n_tag           = norm_tag(self.__dtd)
        n_splitter      = norm_splitter(self.__dtd, self.__relation_fl)
        u               = utils()
        depgraph        = depgraph_heur(matching_method)

        #enumerate if there is no id in the <math> tag
        mts = OrderedDict()
            
        #for xhtml, enumerate mathtag; for xml, enumerate expressiontag; for math_new, enumerate the lines
        for gmid, mt in maths.iteritems():
            #replace <m:math> with <math>
            mt_string_initial = n_arxiv.remove_math_prefix(etree.tostring(mt))

            #remove annotation, attributes, and finally get rid the <math> tag
            mt_string_formatted = n_arxiv.remove_annotation(etree.parse(StringIO(self.__dtd + mt_string_initial)).getroot())
            mt_string_formatted = n_attribute.normalize(mt_string_formatted)

            #normalize mrow
            mt_string_formatted = n_mrow.normalize(mt_string_formatted) 

            #remove fences
            mt_string_formatted = etree.tostring(n_outer_fence.remove_outer_fence(etree.parse(StringIO(self.__dtd + mt_string_formatted)).getroot()))[6:-7]

            #expand maths (normalize tags and/or case)
            expanded = n_tag.normalize_tags('<math>%s</math>' % mt_string_formatted)

            if len(expanded) > 0:
                expanded[-1] = n_mrow.normalize('<math>%s</math>' % expanded[-1])[6:-7]
                expanded.extend([etree.tostring(n_outer_fence.remove_outer_fence(etree.parse(StringIO(self.__dtd + '<math>%s</math>' % exp)).getroot()))[6:-7] for exp in expanded])
            else:
                expanded = [mt_string_formatted]

            mts[gmid] = expanded

            #split around the equality and get the left side subexpressions
            left_subexp = n_splitter.split('<math>%s</math>' % expanded[-1])
            if left_subexp is None: continue

            left_subexp = n_mrow.normalize(left_subexp)[6:-7]
            if not u.is_empty_tag(left_subexp):
                expanded_left = n_tag.normalize_tags(left_subexp)
                expanded_left = [n_mrow.normalize('<math>%s</math>' % exp)[6:-7] for exp in expanded_left]

                mts[gmid].append(left_subexp)
                mts[gmid].extend(expanded_left)

            mts[gmid] = list(set(mts[gmid]))
        edges = depgraph.create_edges(mts)
        return edges

