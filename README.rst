# Tribe README 
# Load example= Human 

# Sync database

python manage.py syncdb

# Migrate organisms, genes, genesets, versions tables individually using South

python manage.py migrate <appname(organisms, genes, etc)>

# Add new organism = Human

python manage.py organisms_create_or_update --taxonomy_id=9606 --scientific_name="Homo sapiens" --common_name="Human"

# Add gene Cross-Reference Databases 

python manage.py genes_add_xrdb --name=Entrez --URL=http://www.ncbi.nlm.nih.gov/gene/_REPL_
python manage.py genes_add_xrdb --name=Ensembl --URL=http://www.ensembl.org/Gene/Summary?g=_REPL_

#NEXT STEPS DOWNLOAD GENE_INFO, UNZIP, ADD TO DATABASE FOR EACH ORGANISM

#HUMAN
wget -P data/ -N ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
gunzip -c data/Homo_sapiens.gene_info.gz > data/Homo_sapiens.gene_info
python manage.py genes_load_geneinfo --geneinfo_file=data/Homo_sapiens.gene_info --taxonomy_id=9606 --systematic_col=2 --symbol_col=2

