from io import StringIO
from itertools import combinations
import time

# If you don't have these modules, run:
#    python -m pip install neo4j networkx requests
import requests
from neo4j import GraphDatabase
import networkx as nx

#Read in a cluster exported from cytoscape as a graphml file to produce Graph P

#Extract the gene IDs from the cluster as gene names in the gene list

#Query the repotrialDB to produce graphml Graph R
	#Extract the genes, the proteins encoded by the genes
	#Extract the drugs_has_target for those proteins
	#Extract the disorders associated with a gene

#Merge R and P on gene name

#Write out the merged graph as a file



