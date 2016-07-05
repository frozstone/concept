from lxml import etree, objectify
from collections import OrderedDict
from copy import deepcopy
from mathmlcontent_to_string import MathML2String
from unify_prolog import UnifiableProlog

#INPUT:  one math expression
#OUTPUT: n (depth of the input) unified math expressions

class Unification:
    def __parse(self, mt_str):
        return etree.fromstring(mt_str)

    def __remove_children(self, mt_xml):
        for child in mt_xml.getchildren():
            mt_xml.remove(child)
        return True

    def __level_to_subexps(self, mt_xml):
        level_subexps = OrderedDict()
        level = 1
        while True:
            subexps = mt_xml.xpath("//*[count(ancestor::*) = %d]" % level)

            if len(subexps) == 0: break
            level_subexps[level] = []
            for exp in subexps:
                if len(exp) > 0: 
                    level_subexps[level].append(exp)
            level += 1
        return level_subexps

    def __get_subexps(self, mt_xml, signature):
        level_subexps = self.__level_to_subexps(mt_xml)

        level_unif = OrderedDict()
        #Descendingly order the level_subexps
        level_subexps = OrderedDict(sorted(level_subexps.iteritems(), key = lambda dt: dt[0], reverse = True))

        for level, subexps in level_subexps.iteritems():
            level_unif[level] = []
            for oldexp in subexps:
                oldexp_copied = deepcopy(oldexp) 
                #1. Enclose the current tag with <semantics>
                exp = etree.Element("semantics")
                exp.insert(0, oldexp_copied)
                #2. Rename the tag (mo -> mo, otherwise into mi)
                if (exp.tag == "csymbol" or exp.tag == "ci") and exp.text.isalnum() and not exp.text.isdigit():
                    exp.text = "%s_%s" % (exp.text, signature)
                    exp.tag = "ci"
                level_unif[level].append(exp)
        return level_unif


    def __print_subexps(self, level_unif):
        for k, v in level_unif.iteritems():
            print k
            for val in v:
                print etree.tostring(val, pretty_print=True)

    def __handle_qvar(self, mt_str):
        qvar_map = {}
        mt_xml = etree.fromstring(mt_str)
        qvar_num = 1
        for qvar_ele in mt_xml.xpath(".//*[local-name() = 'qvar']"):
            if qvar_ele.text not in qvar_map:
                new_text = "QVAR%s" % qvar_num
                qvar_map[qvar_ele.text] = new_text
                qvar_num += 1
            qvar_ele.text = qvar_map[qvar_ele.text]
        return etree.tostring(mt_xml)

    def align(self, mt_str_a, mt_str_b):
        '''
            Assuming mt_xml_a and mt_xml_b are from the same template
            mt_xml_a : query
            mt_xml_b : retrieved
        '''
        mt_xml_a = etree.fromstring(self.__handle_qvar(mt_str_a))
        mt_xml_b = etree.fromstring(mt_str_b)
        mt_xml_tounify_a = deepcopy(mt_xml_a)
        mt_xml_tounify_b = deepcopy(mt_xml_b)

        level_unif_a = self.__get_subexps(mt_xml_tounify_a, 1)
        level_unif_b = self.__get_subexps(mt_xml_tounify_b, 2)

        #descendingly order
        level_unif_a = sorted(level_unif_a.iteritems(), key = lambda dt: dt[0], reverse = True)
        level_unif_b = sorted(level_unif_b.iteritems(), key = lambda dt: dt[0])
        
        str_flattener_a = MathML2String(1, True)
        str_flattener_b = MathML2String(2, False)

        unif = UnifiableProlog("./unify.pl")

#        print etree.tostring(mt_xml_tounify_a)
        mt_str_a, mapping_invalid, index_invalid = str_flattener_a.convert(etree.ElementTree(mt_xml_tounify_a), {}, 0)
#        print index_invalid, mapping_invalid
        for level_b, exps_b in level_unif_b:
            for exp_b in exps_b:
                mapping_invalid_b = deepcopy(mapping_invalid)
                mt_str_b, _, _ = str_flattener_b.convert(etree.ElementTree(exp_b), mapping_invalid_b, index_invalid)
                if mt_str_b == "": return None, False
                is_aligned = unif.is_unified(mt_str_a, mt_str_b)
                if is_aligned: 
                    return level_b, True
        return None, False

