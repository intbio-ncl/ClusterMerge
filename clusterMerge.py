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
def get_repodb_subgraph_given_genes(gene_ids):
	#Connect to RepotrialDB
	connect_url = "bolt://repotrial.bioswarm.net:8687"
	username = "neo4j"
	password = "repodb"
	driver = GraphDatabase.driver(connect_url, auth=(username, password))
	
	repodb_ids = ["entrez.{}".format(i) for i in gene_ids]
	print("Repodb ids ",repodb_ids) 
	
	#Format the query string
	query = """
    UNWIND {repodb_ids} as i
    MATCH x (gene:Gene {primaryDomainId:i})
    RETURN x
    """
	
	print (query)
	
	#Execute the query
	#with driver.session() as session:
	#	for result in session.run(query, repodb_ids=repodb_ids):
	#		print(result)
	
	#How do I populate R from the query results?
	R = nx.Graph()
	return R
	
	
#Main

if __name__ == "__main__":
	#Read in a cluster exported from cytoscape as a graphml file to produce Graph P
	print("reading Graph")
	P = nx.Graph()
	P = nx.read_graphml('./cluster.graphml')
	print("There are {} nodes in the graph".format(P.number_of_nodes()))
	print("There are {} edges in the graph".format(P.number_of_edges()))

	#Extract the gene IDs from the cluster as gene names in the gene list
	gene_ids = [data["name"] for _, data in P.nodes (data=True)]
	#print (gene_ids)

	#Query the repotrialDB to produce graphml Graph R
	R = nx.Graph()
	R = get_repodb_subgraph_given_genes(gene_ids)



#Old Code

#print(list(P.nodes))
#print()
#for node, data in P.nodes(data=True):
#	print(node, data)

#for gene in nx.get_node_attributes(P,"ApprovedSymboles"):
#	print (gene.values())

