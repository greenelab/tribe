from genes.models import Gene, CrossRef, CrossRefDB


def translate_genes(id_list = None, from_id = None, to_id = None, organism = None):
    """
    Pass a list of identifiers (id_list), the name of the database ('Entrez', 'Symbol', 'Standard name', 'Systematic name' or a loaded crossreference database) that you wish to translate from, and the name of the database that you wish to translate to.
    """
    ids = set(id_list)
    not_found = set() # Initializing set of identifiers not found by this translate_genes method
    #let's get the map of from_ids to the gene pks
    from_ids = None

    if organism is not None:
        gene_objects_manager = Gene.objects.filter(organism__scientific_name=organism)
    else:
        gene_objects_manager = Gene.objects

    if (from_id == 'Entrez'):
        int_list = []
        for x in ids:
            try:
                int_list.append(int(x))
            except(ValueError):
                not_found.add(x)
        ids = set(int_list)
        from_ids = gene_objects_manager.filter(entrezid__in=ids).values_list('entrezid', 'id')
    elif (from_id == 'Systematic name'):
        from_ids = gene_objects_manager.filter(systematic_name__in=ids).values_list('systematic_name', 'id')
    elif (from_id == 'Standard name'):
        from_ids = gene_objects_manager.filter(standard_name__in=ids).values_list('standard_name', 'id')
    elif (from_id == 'Symbol'): #TODO: Rene, why does this use the same query? Isn't Symbol defined as some sort of function of standard and systematic?
        from_ids = gene_objects_manager.filter(standard_name__in=ids).values_list('standard_name', 'id')
    else: #a crossreference db?
        xrdb = CrossRefDB.objects.get(name=from_id)
        from_ids = CrossRef.objects.filter(crossrefdb=xrdb).values_list('xrid', 'gene__id')
    from_id_map = {} # from to gene__id
    gene_ids = []
    for item in from_ids:
        from_id_map[item[0]] = item[1]
        gene_ids.append(item[1])

    #now let's figure out what we need to go to:
    to_ids = None
    if (to_id == 'Entrez'):
        to_ids = Gene.objects.filter(id__in=gene_ids).values_list('id', 'entrezid')
    elif (to_id == 'Systematic name'):
        to_ids = Gene.objects.filter(id__in=gene_ids).values_list('id', 'systematic_name')
    elif (to_id == 'Standard name'):
        to_ids = Gene.objects.filter(id__in=gene_ids).values_list('id', 'standard_name')
    elif (to_id == 'Symbol'):
        to_ids = Gene.objects.filter(id__in=gene_ids).values_list('id', 'systematic_name')
    else: #a crossreference db?
        xrdb = CrossRefDB.objects.get(name=to_id)
        to_ids = CrossRef.objects.filter(crossrefdb=xrdb).values_list('gene__id', 'xrid')
    to_id_map = {}
    for item in to_ids:
        if not item[0] in to_id_map:
            to_id_map[item[0]] = [item[1],]
        else:
            to_id_map[item[0]].append(item[1])


    from_to = {}
    for item in ids:
        try:
            gene_id = from_id_map[item]
        except KeyError:
            not_found.add(item)
            continue
        to_id = to_id_map[gene_id]
        from_to[item] = to_id
    from_to['not_found'] = list(not_found)
    return from_to
