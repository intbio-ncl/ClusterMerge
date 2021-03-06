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
	OPTIONAL MATCH (gene)<-[peg:ProteinEncodedBy]-(pro:Protein)
	OPTIONAL MATCH (pro)<-[dht:DrugHasTarget]-(drug)
	OPTIONAL MATCH (drug)-[dsim:MoleculeSimilarityMolecule]-(drug1) WHERE dsim.morganR2 > 0.5
	OPTIONAL MATCH (gene)-[gawd:GeneAssociatedWithDisorder]-(disorder)
    RETURN gene, peg, pro, drug, disorder, dht, gawd, dsim, drug1
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

			drug = result["drug"]
			if drug:
				drug_id = drug['primaryDomainId']
				R.add_node(drug_id, **flatten(drug))
				
			drug1 = result["drug1"]
			if drug1:
				drug1_id = drug1['primaryDomainId']
				R.add_node(drug1_id, **flatten(drug1))
				
				
				
			disorder = result["disorder"]
			if disorder:
				disorder_id = disorder["primaryDomainId"]
				R.add_node(disorder_id, **flatten(disorder))
			
			gawd = result["gawd"]
			if gawd:
				R.add_edge(gene_id, disorder_id, **flatten(gawd))
				
			dsim = result["dsim"]
			if dsim:
				R.add_edge(drug_id, drug1_id, **flatten(dsim))

			dht = result["dht"]
			if dht:
				R.add_edge(drug_id, pro_id, **flatten(dht))

	return R
	
	
#Main

if __name__ == "__main__":
	protein_list_file = "gene_list.txt"
	with open(protein_list_file, "r") as f:
		prey_list = {f"uniprot.{i.strip()}" for i in f}

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
		data.pop("SUID")
		data.pop("selected")
		data.pop("shared name")
		data.pop("shared interaction")
		data = {"".join(word.capitalize() for word in k.split(" ")):v for k,v in data.items()}
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
			if node in prey_list:
				graphics[node] = {"fill" : "#D11D53"}
			else:
				graphics[node] = {"fill" : "#00FF00"}
			labels[node] = node.split(".")[1]
		# If the node is a Gene and it has a symbol, use the symbol.
		elif data['type'] == "Gene":
			graphics[node] = {"fill" : "#FFB6C1"}
			if data.get("approvedSymbol") not in [None, "-"]:
				labels[node] = data["approvedSymbol"]
		
		elif data['type'] == "Disorder":
			graphics[node] = {"fill" : "#FF7F00"}

		elif data['type'] in ["BiotechDrug", "SmallMoleculeDrug"]:
			graphics[node] = {"fill" : "#34A4EB"}


	# Set the labels.
	nx.set_node_attributes(R, graphics, name="graphics")
	nx.set_node_attributes(R, labels, name="name")

	# Save the graph
	nx.write_gml(R, "cluster_out.gml")