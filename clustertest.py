from os                 import path, listdir
from AnnReader          import AnnReader
from MathReader         import MathReader
from WordSim            import WordSim
from Cluster            import Cluster
from HeurDep            import HeurDep
from utilities.utils    import Link_Types, Matching_Methods
from pickle             import load, dump
from lxml               import etree
from collections        import OrderedDict
import numpy as np
import networkx as nx
import community

labels = {0:"0",1:"1",2:"2"}
edges = np.zeros(shape=(4,4))


G = nx.Graph()
G.add_edge(0,1,weight=2)
G.add_edge(1,2,weight=1000)
nx.to_numpy_matrix(G, nodelist=[0,1,2])

edges[0,1]=100
edges[1,2]=100
edges[2,3]=100

edges = np.matrix(edges)

ug = nx.Graph()
ug.add_weighted_edges_from([(0,1,0.1), (1,2,100), (2,3,0.1)])

g = nx.from_numpy_matrix(edges)
p = community.best_partition(ug, resolution = 4)
print p

from sklearn import cluster
s = cluster.SpectralClustering(n_clusters = 2, eigen_solver =None, affinity = "nearest_neighbors", n_neighbors=1)
p = s.fit_predict(edges)
