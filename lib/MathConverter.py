from lxml import etree

class MathConverter:
    def __prefix_to_mathcontent_rec(self, prefix):
        if "(" not in prefix:
            return etree.Element(prefix)

        start_open_parenth = prefix.index("(")
        tag = prefix[:start_open_parenth]

        doc = etree.Element(tag)
        if tag == "ci" or tag == "cn":
            doc.text = prefix[start_open_parenth+1:len(prefix) - 1]
            return doc

        #get the arguments
        arguments = []
        start_argument  = start_open_parenth + 1
        n_open_parenths = 1
        for idx in range(start_open_parenth + 1, len(prefix)):
            if prefix[idx] == '(':
                n_open_parenths += 1
                continue
            if prefix[idx] == "," and n_open_parenths == 1:
                arguments.append(prefix[start_argument:idx])
                start_argument = idx + 1
                continue
            if prefix[idx] == ")":
                n_open_parenths -= 1
                if n_open_parenths == 0:
                    arguments.append(prefix[start_argument:idx])
                if n_open_parenths == 0 and idx < len(prefix) - 1: return "Invalid Math"
    
        for arg in arguments:
            ch = self.__prefix_to_mathcontent_rec(arg.strip())
            doc.append(ch)
        return doc


    def prefix_to_mathcontent(self, prefix):
        #add math and annotation-xml at the beginning
        doc = etree.Element("math")
        ann = etree.Element("annotation-xml", encoding="MathML-Content")
        mainbody = self.__prefix_to_mathcontent_rec(prefix) 
        ann.append(mainbody)
        doc.append(ann)
        return doc

    def __mathcontent_to_prefix_rec(self, x_mcontent):
        is_text_empty = (x_mcontent.text == None or x_mcontent.text == "")
        
        if len(x_mcontent) == 0 and is_text_empty: return ""
        if len(x_mcontent) == 0 and not is_text_empty: return "(%s)" % x_mcontent.text

        prefix = "(%s)" % ", ".join("%s%s" % (ch.tag, self.__mathcontent_to_prefix_rec(ch)) for ch in x_mcontent)
        return prefix

    def mathcontent_to_prefix(self, mcontent):
        #math from phml is directy under <math>
        doc = etree.fromstring(mcontent)
        prefix = "%s%s" % (doc[0].tag, self.__mathcontent_to_prefix_rec(doc[0]))
        return prefix

