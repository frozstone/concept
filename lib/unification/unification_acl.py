from lxml           import etree
from unification    import Unification

class UnificationACL:
    def __extract_mathmlcontent(self, mt_xml):
        ann_xmls = mt_xml.xpath(".//*[local-name() = 'annotation-xml']")
        if len(ann_xmls) > 0:
            return ann_xmls[-1]
        else:
            return None


    def __unify(self, mt_xml_query, mt_xml_result):
        ann_xml_query       = self.__extract_mathmlcontent(mt_xml_query)

        ann_xml_query.tag   = "semantics"
        mt_str_query        = etree.tostring(ann_xml_query)

        ann_xml_res         = self.__extract_mathmlcontent(mt_xml_result)
        if ann_xml_res is None: return False
        ann_xml_res.tag     = "semantics"
        mt_str_res          = etree.tostring(ann_xml_res)

        u = Unification()
        matchlevel, isunify = u.align(mt_str_query, mt_str_res)
        return isunify

    def unify_string(self, mt_str_query, mt_str_result):
        mt_xml_query = etree.fromstring(mt_str_query)
        mt_xml_result = etree.fromstring(mt_str_result)
        return self.__unify(mt_xml_query, mt_xml_result)
