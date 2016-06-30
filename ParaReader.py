from collections    import OrderedDict
from lxml           import etree
from nltk           import word_tokenize

class ParaReader:
    __xpaper = None

    def __init__(self, xml_flpath):
        self.__xpaper = etree.parse(xml_flpath)

    def __get_xml_text(self, xelement):
        etree.strip_tags(xelement, "*")
        para = xelement.text.strip()
        para = " ".join(token for token in word_tokenize(para) if token.isalnum())
        return para

    def get_paragraph_for_math(self, math_infty_id):
        mml = self.__xpaper.xpath(".//*[local-name() = 'math' and @id = '%s']" % math_infty_id)[0]
        parent = mml.getparent()

        while parent.tag != "Para":
            parent = parent.getparent()

        paratext_ele = parent.xpath(".//ParaText")[0]
        return self.__get_xml_text(paratext_ele)

