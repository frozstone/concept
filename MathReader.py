from lxml           import etree
from os             import path, listdir
from collections    import OrderedDict

class MathReader:
    def __get_filename(self, xml_dir, pname):
        for fl in listdir(xml_dir):
            if fl.startswith(pname) and fl.endswith("_gd_output.xml"): return path.join(xml_dir, fl)

    def __remove_mathml_content(self, m_xml):
        cmls = m_xml.xpath(".//*[local-name() = 'annotation-xml']")
        for c in cmls:
            c.getparent().remove(c)

    def __strip_semantics_tag(self, m_xml):
        etree.strip_tags(m_xml, "{http://www.w3.org/1998/Math/MathML}semantics")

    def read_maths(self, xml_dir, pname):
        flpath = self.__get_filename(xml_dir, pname)

        parser = etree.XMLParser(remove_blank_text = True)
        xdoc  = etree.parse(flpath, parser)
        maths = xdoc.xpath(".//*[local-name() = 'math']")
        
        fl_basename     = path.basename(flpath)
        fl_basename     = fl_basename.split("_")[0]

        math_dict       = OrderedDict()
        math_local_id   = 1
        for m in maths:
            mid = "MATH_%s_%s" % (fl_basename, math_local_id)
            math_local_id += 1

            m.tail = ""
            self.__strip_semantics_tag(m)
            self.__remove_mathml_content(m)
            math_dict[mid] = m
        return math_dict

    def read_complete_maths(self, xml_dir, pname):
        flpath = self.__get_filename(xml_dir, pname)

        parser = etree.XMLParser(remove_blank_text = True)
        xdoc  = etree.parse(flpath, parser)
        maths = xdoc.xpath(".//*[local-name() = 'math']")
        
        fl_basename     = path.basename(flpath)
        fl_basename     = fl_basename.split("_")[0]

        math_dict       = OrderedDict()
        math_local_id   = 1
        for m in maths:
            mid = "MATH_%s_%s" % (fl_basename, math_local_id)
            math_local_id += 1

            m.tail = ""
            self.__strip_semantics_tag(m)
            math_dict[mid] = m
        return math_dict

