from os import path, listdir

class AnnReader:
    def __get_textual_desc(self, block, word_map):
        word_ranges = block[1:-1]
        words = []
        for wr in word_ranges.split(","):
            if "-" not in wr: 
                words.append(word_map[wr])
            else:
                start_idx, end_idx = [int(i) for i in wr.split("-")]
                segments = []
                for idx in range(start_idx, end_idx+1):
                    segments.append(word_map[str(idx)])
                words.append(" ".join(segments))
        return " ".join(words)

    def __get_math_desc(self, m_ln_idx, lines, word_map):
        descriptions = []
        
        m_ln_idx += 1
        ln = lines[m_ln_idx].strip()
        while ln != "":
            descriptions.append(self.__get_textual_desc(ln, word_map))
            m_ln_idx += 1
            ln = lines[m_ln_idx].strip()
        return descriptions

    def __read_ann(self, flpath):
        lines       = open(flpath).readlines()
        word_map    = {} 
        for l in lines:
            if l.strip() == "" or "\t" not in l: continue
            tokens          = l.strip().split("\t")
            w_idx           = tokens[0]
            w_text          = "\t".join(tokens[1:])
            word_map[w_idx] = "MATH" if "MATH_" in w_text else w_text

        desc_map    = {}
        for i, l in enumerate(lines):
            if l.startswith("MATH"):
                descriptions = self.__get_math_desc(i, lines, word_map)
                #if len(descriptions) == 0: continue
                desc_map[l.strip()] = descriptions        
        return desc_map

    def get_paper_ann(self, ann_dirpath, papername):
        desc_map = {}
        for fl in listdir(ann_dirpath):
            if not fl.startswith(papername): continue
            desc_map.update(self.__read_ann(path.join(ann_dirpath, fl)))
        return desc_map

