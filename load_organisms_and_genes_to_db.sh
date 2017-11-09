#!/bin/bash

# Make sure the script is being run from the directory where this file
# and 'manage.py' are
script_directory=`dirname "${BASH_SOURCE[0]}" | xargs realpath`
cd $script_directory

# Create organism records
python manage.py organisms_create_or_update --taxonomy_id=9606 \
    --scientific_name="Homo sapiens" --common_name="Human"
python manage.py organisms_create_or_update --taxonomy_id=4932 \
    --scientific_name="Saccharomyces cerevisiae" --common_name="S. cerevisiae"
python manage.py organisms_create_or_update --taxonomy_id=10090 \
    --scientific_name="Mus musculus" --common_name="Mouse"
python manage.py organisms_create_or_update --taxonomy_id=10116 \
    --scientific_name="Rattus norvegicus" --common_name="Rat"
python manage.py organisms_create_or_update --taxonomy_id=6239 \
    --scientific_name="Caenorhabditis elegans" --common_name="C. elegans"
python manage.py organisms_create_or_update --taxonomy_id=3702 \
    --scientific_name="Arabidopsis thaliana" --common_name="Arabidopsis"
python manage.py organisms_create_or_update --taxonomy_id=7227 \
    --scientific_name="Drosophila melanogaster" --common_name="Fruit fly"
python manage.py organisms_create_or_update --taxonomy_id=7955 \
    --scientific_name="Danio rerio" --common_name="Zebrafish"
python manage.py organisms_create_or_update --taxonomy_id=208964 \
    --scientific_name="Pseudomonas aeruginosa" --common_name="Pseudomonas aeruginosa"

# Create records for cross-reference databases (such as Ensembl)
python manage.py genes_add_xrdb --name=Ensembl \
    --URL=http://www.ensembl.org/Gene/Summary?g=_REPL_
python manage.py genes_add_xrdb --name=Entrez \
    --URL=http://www.ncbi.nlm.nih.gov/gene/_REPL_
python manage.py genes_add_xrdb --name=HGNC \
    --URL=http://www.genenames.org/data/hgnc_data.php?hgnc_id=_REPL_
python manage.py genes_add_xrdb --name=HPRD \
    --URL=http://www.hprd.org/protein/_REPL_
python manage.py genes_add_xrdb --name=MGI \
    --URL=http://www.informatics.jax.org/searches/accession_report.cgi?id=MGI:_REPL_
python manage.py genes_add_xrdb --name=MIM \
    --URL=http://www.ncbi.nlm.nih.gov/omim/_REPL_
python manage.py genes_add_xrdb --name=SGD \
    --URL=http://www.yeastgenome.org/cgi-bin/locus.fpl?dbid=_REPL_
python manage.py genes_add_xrdb --name=TAIR \
    --URL=http://www.arabidopsis.org/servlets/TairObject?type=locus&name=_REPL_
python manage.py genes_add_xrdb --name=UniProtKB \
    --URL=http://www.uniprot.org/uniprot/_REPL_
python manage.py genes_add_xrdb --name=WormBase \
    --URL=http://www.wormbase.org/db/gene/gene?name=_REPL_
python manage.py genes_add_xrdb --name=RGD \
    --URL=http://rgd.mcw.edu/tools/genes/genes_view.cgi?id=_REPL_
python manage.py genes_add_xrdb --name=FLYBASE \
    --URL=http://flybase.org/reports/_REPL_.html
python manage.py genes_add_xrdb --name=ZFIN \
    --URL=http://zfin.org/action/marker/view/_REPL_
python manage.py genes_add_xrdb --name=Vega \
    --URL=http://vega.sanger.ac.uk/Homo_sapiens/Gene/Summary?g=_REPL_
python manage.py genes_add_xrdb --name="IMGT/GENE-DB" \
    --URL=http://www.imgt.org/IMGT_GENE-DB/GENElect?query=2+_REPL_&species=_SPEC_
python manage.py genes_add_xrdb --name="miRBase" \
    --URL=http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=_REPL_
python manage.py genes_add_xrdb --name=PseudoCAP \
    --URL=http://www.pseudomonas.com/getAnnotation.do?locusID=_REPL_

# Next steps download gene_info files, unzip them, and load them to the
# database for each organism

# Human
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
gunzip -c data/Homo_sapiens.gene_info.gz > \
    data/Homo_sapiens.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Homo_sapiens.gene_info \
    --taxonomy_id=9606 \
    --systematic_col=2 \
    --symbol_col=2

# Yeast
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Fungi/Saccharomyces_cerevisiae.gene_info.gz
gunzip -c data/Saccharomyces_cerevisiae.gene_info.gz > \
    data/Saccharomyces_cerevisiae.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Saccharomyces_cerevisiae.gene_info \
    --taxonomy_id=4932 \
    --gi_tax_id=559292 \
    --systematic_col=3 \
    --symbol_col=2

# Mouse
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Mus_musculus.gene_info.gz
gunzip -c data/Mus_musculus.gene_info.gz > \
    data/Mus_musculus.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Mus_musculus.gene_info \
    --taxonomy_id=10090 \
    --systematic_col=2 \
    --symbol_col=2

# Rat
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Rattus_norvegicus.gene_info.gz
gunzip -c data/Rattus_norvegicus.gene_info.gz > \
    data/Rattus_norvegicus.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Rattus_norvegicus.gene_info \
    --taxonomy_id=10116 \
    --systematic_col=2 \
    --symbol_col=2

# C. elegans
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Invertebrates/Caenorhabditis_elegans.gene_info.gz
gunzip -c data/Caenorhabditis_elegans.gene_info.gz > \
    data/Caenorhabditis_elegans.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Caenorhabditis_elegans.gene_info \
    --taxonomy_id=6239 \
    --systematic_col=3 \
    --symbol_col=2

# Load Wormbase
# Find latest version of WormBase here: http://www.wormbase.org/about/release_schedule#102--10-1
python manage.py genes_load_wb \
    --wb_url=ftp://ftp.wormbase.org/pub/wormbase/releases/WS243/species/c_elegans/PRJNA13758/c_elegans.PRJNA13758.WS243.xrefs.txt.gz \
    --taxonomy_id=6239

# Arabidopsis
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Plants/Arabidopsis_thaliana.gene_info.gz
gunzip -c data/Arabidopsis_thaliana.gene_info.gz > \
    data/Arabidopsis_thaliana.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Arabidopsis_thaliana.gene_info \
    --taxonomy_id=3702 \
    --systematic_col=3 \
    --symbol_col=2

# Fly
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Invertebrates/Drosophila_melanogaster.gene_info.gz
gunzip -c data/Drosophila_melanogaster.gene_info.gz > \
    data/Drosophila_melanogaster.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Drosophila_melanogaster.gene_info \
    --taxonomy_id=7227 \
    --systematic_col=3 \
    --symbol_col=2

# Zebrafish
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Non-mammalian_vertebrates/Danio_rerio.gene_info.gz
gunzip -c data/Danio_rerio.gene_info.gz > \
    data/Danio_rerio.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Danio_rerio.gene_info \
    --taxonomy_id=7955 \
    --systematic_col=2 \
    --symbol_col=2

# Pseudomonas
wget -P data/ -N \
    ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Archaea_Bacteria/Pseudomonas_aeruginosa_PAO1.gene_info.gz
gunzip -c data/Pseudomonas_aeruginosa_PAO1.gene_info.gz > \
    data/Pseudomonas_aeruginosa_PAO1.gene_info
python manage.py genes_load_geneinfo \
    --geneinfo_file=data/Pseudomonas_aeruginosa_PAO1.gene_info \
    --taxonomy_id=208964 \
    --systematic_col=3 \
    --symbol_col=2 \
    --put_systematic_in_xrdb=PseudoCAP

# Uniprot Identifiers
wget -P data/ -N \
    ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/idmapping.dat.gz
zgrep "GeneID" data/idmapping.dat.gz > data/uniprot_entrez.txt
python manage.py genes_load_uniprot --uniprot_file=data/uniprot_entrez.txt


# Load gene history for all organisms
wget -qO - "ftp://ftp.ncbi.nih.gov/gene/DATA/gene_history.gz" \
    | zcat > data/gene_history

# Human
python manage.py genes_load_gene_history \
    data/gene_history 9606 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Yeast
python manage.py genes_load_gene_history \
    data/gene_history 4932 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Mouse
python manage.py genes_load_gene_history \
    data/gene_history 10090 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Rat
python manage.py genes_load_gene_history \
    data/gene_history 10116 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Worm
python manage.py genes_load_gene_history \
    data/gene_history 6239 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Arabidopsis
python manage.py genes_load_gene_history \
    data/gene_history 3702 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Fly
python manage.py genes_load_gene_history \
    data/gene_history 7227 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Zebrafish
python manage.py genes_load_gene_history \
    data/gene_history 7955 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4

# Pseudomonas
python manage.py genes_load_gene_history \
    data/gene_history 208964 \
    --tax_id_col=1 \
    --discontinued_id_col=3 \
    --discontinued_symbol_col=4


# Note: Gene Ontology, KEGG, and Disease Ontology (from OMIM) gene sets are
# now processed and saved via the annotation refinery:
# https://github.com/greenelab/annotation-refinery
