from collections    import OrderedDict
from lxml           import etree
from nltk           import word_tokenize
from os             import path

class ParaReader:
    __pname     = None
    __xpaper    = None
    __para_map  = None

    def __init__(self, xml_flpath):
        flname        = path.basename(xml_flpath)
        self.__pname  = flname.replace("_gd_output.xml", "")
        self.__xpaper = etree.parse(xml_flpath)
        self.__get_paragraph_for_math()

    def __get_xml_text(self, xelement):
        etree.strip_tags(xelement, "*")
        para = xelement.text.strip()
        para = " ".join(token for token in word_tokenize(para) if token.isalnum())
        return para

    def __symbolize_mathml(self, element, start_id):
        infty_ids = []
        for mt in element.xpath(".//*[local-name() = 'math']"):
            mid         = "MATH_%s_%s" % (self.__pname, start_id)
            mt.tail     = "%s%s" % (mid, mt.tail)

            infty_ids.append(mt.attrib["id"])
            start_id   += 1
        etree.strip_elements(element, "{http://www.w3.org/1998/Math/MathML}math", with_tail = False)
        return infty_ids, start_id

    def __get_paragraph_for_math(self):
        para_xmls   = self.__xpaper.xpath(".//Para")
        start_id    = 1
        for p in para_xmls:
            clean_lines = []
            infty_ids   = []
            lines       = p.xpath(".//Line")
            for ln in lines:
                iids_local, start_id  = self.__symbolize_mathml(ln, start_id)
                infty_ids.extend(iids_local)
                clean_lines.append(ln.text.replace("\n", ""))
            
            para_text   = " ".join(clean_lines)
            for m in mids:
                self.__para_map[m] = para_text
        return True
            
    def get_paragraph_for_math(self, math_infty_id):
        return self.__para_map[math_infty_id]

