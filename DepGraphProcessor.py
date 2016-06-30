from utilities.utils    import Link_Types
from collections        import OrderedDict
from lxml               import etree


class DepGraphProcessor:
    __math_map = None
    __desc_map = None
    __para_map = None
    __depgraph = None

    def __init__(self, math_map, desc_map, para_map, depgraph):
        self.__math_map = math_map
        self.__desc_map = desc_map
        self.__para_map = para_map
        self.__depgraph = depgraph

    def __get_descriptions(self, mid):
        return self.__desc_map[mid] if mid in self.__desc_map else []

    def __rename_nodes(self, maths, desc_map, para_map, depgraph):
        """
            the parameters are the output of compress_depgraph
        """
        new_math_map = OrderedDict()
        new_desc_map = OrderedDict()
        new_para_map = OrderedDict()
        new_depgraph = OrderedDict()

        new_old_math_map = {}
        old_new_math_map = {}

        idx = 0
        for v in maths:
            mid = "MATH_%d" % idx
            new_old_math_map[mid] = v
            old_new_math_map[v]   = mid

            new_math_map[mid] = self.__math_map[v]
            new_desc_map[mid] = desc_map[v]
            new_para_map[mid] = para_map[v]
            idx += 1
            
        for k, vs in depgraph.iteritems():
            new_depgraph[old_new_math_map[k]] = []
            for v, vt in vs:
                new_depgraph[old_new_math_map[k]].append((old_new_math_map[v], vt))
        return new_math_map, new_desc_map, new_para_map, new_depgraph, old_new_math_map


    def compress_depgraph(self):
        new_maths       = []
        new_maths_rev   = OrderedDict()
        new_desc_map    = OrderedDict()
        new_para_map    = OrderedDict()
        new_depgraph    = OrderedDict()

        # clusters all math with relation of "exp" and "simexp" together
        for k, vs in self.__depgraph.iteritems():
            if k in new_maths_rev: continue
            same_groups     = [k] + [v for v, vtype in vs if vtype is Link_Types.exp or vtype is Link_Types.simexp]
            representative  = sorted(same_groups, key = lambda v: len(etree.tostring(self.__math_map[v])), reverse = True)[0]

            new_maths.append(representative)
            new_desc_map[representative] = []
            new_para_map[representative] = []
            new_depgraph[representative] = set()

            for v in same_groups: 
                new_maths_rev[v] = representative
                new_desc_map[representative].extend(self.__get_descriptions(v))
                new_para_map[representative].append(self.__para_map[v])

        # populate new dependency graph
        for k in new_depgraph.keys():
            direct_neighbors = [k] + [v for v, vt in self.__depgraph[k] if vt is Link_Types.exp or vt is Link_Types.simexp]
            component_ids = set()
            components    = []
            for v in direct_neighbors:
                comps = [(new_maths_rev[v1] if v1 in new_maths_rev else v1, v1t) for v1, v1t in self.__depgraph[v] if v1 not in component_ids and (v1t is Link_Types.comp or v1t is Link_Types.simcomp)]
                new_depgraph[k].update(comps)

                component_ids.update(v1 for v1, v1t in comps)

        # populate math that are only a single symbol
        for k, v in self.__math_map.iteritems():
            if k in new_maths_rev: continue
            new_maths.append(k)
            new_maths_rev[k]= k
            new_desc_map[k] = self.__get_descriptions(k)
            new_para_map[k] = self.__para_map[k]
        return self.__rename_nodes(new_maths, new_desc_map, new_para_map, new_depgraph), new_maths_rev

    def get_roots(self, math_map, depgraph):
        components = set()
        for k, vs in depgraph.iteritems():
            components.update(v for v, vt in vs)

        math_set = set(math_map.keys())
        return math_set.difference(components)

    def get_sink_nodes(self, math_map, depgraph):
        sink_nodes = set()

        # get sink nodes from dep graph
        for k, vs in depgraph.iteritems():
            is_any_comp = any(vt is Link_Types.comp or vt is Link_Types.simcomp for v, vt in vs)
            if not is_any_comp:
                sink_nodes.update([k] + [v for v, vt in vs])
            else:
                if k in sink_nodes: sink_nodes.remove(k)
                for v, vt in vs:
                    if vt is Link_Types.comp or vt is Link_Types.simcomp: sink_nodes.add(v)
                    elif v in sink_nodes: sink_nodes.remove(v)

        # get sink nodes from math_map
        math_all        = set(math_map.keys())
        math_depgraph   = set(depgraph.keys())
        for _, vs in depgraph.iteritems():
            math_depgraph.update(v for v, vt in vs)

        sink_nodes.update(math_all.difference(math_depgraph))
        return sink_nodes

