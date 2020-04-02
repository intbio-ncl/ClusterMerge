from collections.abc import MutableMapping
from io import StringIO
from itertools import combinations
import time

# If you don't have these modules, run:
#    python -m pip install neo4j networkx requests
import requests
from neo4j import GraphDatabase
import networkx as nx


# Helper function to flatten dictionaries
def flatten(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    rtrn = {}
    for k, v in items:
        if isinstance(v, list):
            rtrn[k] = ", ".join(v)
        elif v is None:
            rtrn[k] = "None"
        else:
            rtrn[k] = v

    return rtrn


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
	# Drugs, disorders
	query = """
    UNWIND {repodb_ids} as i
    MATCH (gene:Gene {primaryDomainId:i})
	OPTIONAL MATCH (gene)<-[peg:ProteinEncodedBy]-(pro)
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
			R.add_node(gene_id, **flatten(gene))

			# Changed the query to OPTIONAL MATCH -- this means that, if the 
			# pattern doesn't match, the variables are replaced with None / Null
			pro = result["pro"]
			# Because pro can be Null / None, we check for this and don't want
			# to add anything if not.
			if pro:
				pro_id = pro['primaryDomainId']
				R.add_node(pro_id, **flatten(pro))

			peg = result["peg"]
			# Similarly, peg can be None.
			if peg:
				R.add_edge(pro_id, gene_id, **flatten(peg))

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

	# Query the RepoDB to produce graphml Graph R
	R = get_repodb_subgraph_given_genes(gene_ids)

	# Makes a hash map from node label to name.
	node_id_to_entrez = nx.get_node_attributes(P, "name")

	# This block is merging P.
	for i, j, data in P.edges(data=True):
		i_name = 'entrez.{}'.format( node_id_to_entrez[i])
		j_name = 'entrez.{}'.format( node_id_to_entrez[j])
		data = {"".join(word.capitalize() for word in k.split(" ")):v for k,v in data.items()}
		data.pop("Suid")
		data.pop("Selected")
		R.add_edge(i_name, j_name, **flatten(data), type="IsFunctionallyRelatedTo" )

	# Changing labels.
	labels = {}
	graphics = {}

	# This is changing labels. Some nodes don't have a "type", because they aren't in RepoDB.
	for node, data in R.nodes(data=True):
		if not "type" in data:
			print("Warning: {node} not annotated as it is not present in RepoDB".format(node=node))
			continue
		# If the node is a protein, change the label to the UniProt ID.
		if data['type'] == "Protein":
			graphics[node] = {"fill" : "#00FF00"}
			labels[node] = node.split(".")[1]
		# If the node is a Gene and it has a symbol, use the symbol.
		elif data['type'] == "Gene":
			graphics[node] = {"fill" : "#FFB6C1"}

			if data.get("approvedSymbol") not in [None, "-"]:
				labels[node] = data["approvedSymbol"]
			

	# Set the labels.
	nx.set_node_attributes(R, graphics, name="graphics")
	nx.set_node_attributes(R, labels, name="name")

	# Save the graph
	nx.write_gml(R, "test.gml")