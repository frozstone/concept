import community
import networkx as nx
import matplotlib.pyplot as plt 
from collections import OrderedDict
from lxml import etree

class Cluster:
    def __print_cluster(self, partition, math_map, desc_map):
        n_cluster = max(partition.values())
        clusters  = OrderedDict.fromkeys(range(n_cluster+1))
        for node, cl in partition.iteritems():
            if clusters[cl] is None: clusters[cl] = []
            clusters[cl].append(node)

        mid_prefix = math_map.items()[0][0]
        mid_prefix = mid_prefix[:mid_prefix.rindex("_")]
        for ckey, cnodes in clusters.iteritems():
            print ckey
            for node in cnodes:
                if node == 0: continue
                gmid = "%s_%d" % (mid_prefix, node)
                mml  = math_map[gmid]
                etree.strip_tags(mml, "*")

                desc = desc_map[gmid] if gmid in desc_map else ""

                print mml.text.encode("utf-8"), desc
            print ""

    def comm_detect(self, labels, edges, math_map, desc_map):
        g = nx.from_numpy_matrix(edges)

        partition = community.best_partition(g)
        self.__print_cluster(partition, math_map, desc_map)

        partresult = partition.values()

        pos = nx.spring_layout(g)
        nx.draw_networkx_nodes(g, pos, node_color = partition.values())
        nx.draw_networkx_labels(g, pos, labels, font_size=16)
        nx.draw_networkx_edges(g, pos)
        plt.show()
        
    def comm_detect_g(self, g):
        partition = community.best_partition(g)
        partresult = partition.values()

        pos = nx.spring_layout(g)
        nx.draw_networkx_nodes(g, pos, node_color = partition.values())
        #nx.draw_networkx_labels(g, pos, labels, font_size=16)
        nx.draw_networkx_edges(g, pos)
        plt.show()

