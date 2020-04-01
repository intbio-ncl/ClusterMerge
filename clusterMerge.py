from io import StringIO
from itertools import combinations
import time

# If you don't have these modules, run:
#    python -m pip install neo4j networkx requests
import requests
from neo4j import GraphDatabase
import networkx as nx

#Logic
#Read in a cluster exported from cytoscape as a graphml file to produce Graph P
#Extract the gene IDs from the cluster as gene names in the gene list
#Query the repotrialDB to produce graphml Graph R
	#Extract the genes, the proteins encoded by the genes
	#Extract the drugs_has_target for those proteins
	#Extract the disorders associated with a gene
#Merge R and P on gene name
#Write out the merged graph as a file


	
	
#Main

#Read in a cluster exported from cytoscape as a graphml file to produce Graph P
print("reading Graph")
P = nx.Graph()
P = nx.read_graphml('./cluster.graphml')
print("There are {} nodes in the graph".format(P.number_of_nodes()))
print("There are {} edges in the graph".format(P.number_of_edges()))

#Extract the gene IDs from the cluster as gene names in the gene list
list(P.nodes)


