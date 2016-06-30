from lxml import etree, objectify
import re

class norm_attribute:
    def __remove_attributes_node(self, mt_node):
        if not mt_node.attrib: return True
        for at in mt_node.attrib.keys():
            del mt_node.attrib[at]

    def __remove_attributes_tree(self, mt_tree):
        self.__remove_attributes_node(mt_tree)
        for child in mt_tree:
            self.__remove_attributes_tree(child)

    def __remove_xmlns(self, mt_string):
        mt_string = re.sub(' xmlns="[^"]+"', '', mt_string, count = 1)
        return mt_string

    def normalize(self, mt_string):
        mt_string = self.__remove_xmlns(mt_string)
        mt_tree = etree.fromstring(mt_string)
        self.__remove_attributes_tree(mt_tree)
        objectify.deannotate(mt_tree, cleanup_namespaces=True)
        return etree.tostring(mt_tree)

