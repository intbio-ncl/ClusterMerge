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
    MATCH (gene:Gene {primaryDomainId:i})
	MATCH (gene)<-[peg:ProteinEncodedByGene]-(pro)
    RETURN gene, peg, pro
    """
	
	print (query)
	
	R = nx.Graph()
	
	#Execute the query
	with driver.session() as session:
		for result in session.run(query, repodb_ids=repodb_ids):
			# Imagine result as a hash map. The keys are the variables you had
			# in the return clase of the query.
			gene = result["gene"]  
			# Imagine gene is now a hash map of the node / edge requested, with
			# key:value pairs being attribute_name : attribute_value.

			# The primaryDomainId is most ideal for the node label (we can swap 
			# this out after).
			gene_id = gene["primaryDomainId"]

			# Add node to graph R. **gene is some syntactic sugar. Basically, 
			# add_node takes a label as 0th positional argument, then keyword
			# arguments for the remaining attributes. **gene takes a hash map
			# (e.g., {"geneType": "protein-coding", "displayName": "TMPRSS2"}),
			# and expands it as keyword arguments for the function (i.e.,
			# (geneType = "protein-coding", displayName = "TMPRSS2"))
		
			R.add_node(gene_id, **gene)

			pro = result["pro"]
			pro_id = pro['primaryDomainId']
			R.add_node(pro_id, **pro)

			peg = result["peg"]
			R.add_edge(pro_id, gene_id, **peg)


	#How do I populate R from the query results?
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

