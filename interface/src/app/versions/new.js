/**
 * Each section of the site has its own module. It probably also has
 * submodules, though this boilerplate is too simple to demonstrate it. Within
 * `src/app/home`, however, could exist several additional folders representing
 * additional modules that would then be listed as dependencies of this one.
 * For example, a `note` section could have the submodules `note.create`,
 * `note.delete`, `note.edit`, etc.
 *
 * Regardless, so long as dependencies are managed correctly, the build process
 * will automatically take take of the rest.
 *
 * The dependencies block here is also where component dependencies should be
 * specified, as shown below.
 */
angular.module( 'tribe.versions.new', [
  'ui.router.state',
  'tribe.gene.search',
  'tribe.versions.resource',
  'tribe.versions.directives',
  'tribe.genesets.resource',
  'tribe.publications.resource',
  'tribe.publications.directives'
])

/**
 * Each section or module of the site can also have its own routes. AngularJS
 * will handle ensuring they are all available at run-time, but splitting it
 * this way makes each module more "self-contained".
 */
    .config(function ( $stateProvider ) {
        $stateProvider
            .state( 'use.newversion', {
                url: '/newversion/:creator/:slug/:version',
                views: {
                    "main": {
                        controller: 'NewVersionCtrl',
                        templateUrl: 'versions/new.tpl.html'
                    }
                },
                data: {
                    pageTitle: 'New Version'
                }
            })
            .state( 'use.firstversion', {
                url: '/newversion/:orgslug',
                views: {
                    "main": {
                        controller: 'FirstVersionCtrl',
                        templateUrl: 'versions/new-first-version.tpl.html'
                    }
                },
                data: {
                    pageTitle: 'Add genes'
                }
            })
        ;

    })


    .factory( 'Annotations', function( ) {

        var annotations = {}; // This is the most important one - this dictionary holds each gene's pk as the key
                       // in the dictionary, and then the value for each key is the list of publications
                       // associated with that gene. This is what will be passed to the new version being created.

        var init_annotations = {}; // This will be filled out by annotations passed by previous version.
                                    // Key is the gene id, value is the list of publications.
        var genes = {}; // Holds full information for each genes. Key is gene id, value is gene object.

        // Added and removed genes relative to the previous version
        // For both of these, key is gene id, value is true or false
        var added_genes = {}; 
        var removed_genes = {};

        // Added and removed publications relative to the previous version
        // For both of these, key is gene id, value is list of publications
        var added_pubs = {};
        var removed_pubs = {};

        return {

            clear: function() {
                annotations = {};
                init_annotations = {};
                genes = {};
                added_genes = {};
                removed_genes = {};
                added_pubs = {};
                removed_pubs = {};

            },

            init: function( passed_annotations ) {
                for (var i in passed_annotations ) {
                    gid = passed_annotations[i].gene.id;
                    init_annotations[gid] = passed_annotations[i].pubs;
                    annotations[gid] = passed_annotations[i].pubs;
                    genes[gid] = passed_annotations[i].gene;
                }
            },

            addGene: function( geneObj ) {
                gid = geneObj.id;
                genes[gid] = geneObj;

                if ( init_annotations[gid] ) { 
                // This will get triggered if gene was in initial annotations,
                // was then removed, and then added again via the searchResults factory (not the undoGene function below)
                    delete removed_genes[gid]; // take it out of the removed genes
                } else { // Gene is being added for the first time
                    added_genes[gid] = true;
                }

                annotations[gid] = [];
            },

            removeGene: function( geneObj ) {
            // This function can be called from the 'Version being created' panel 
            // For the function to remove gene from 'New annotations' panel, call function below, undoGene()
                gid = geneObj.id;

                if( init_annotations[gid] ) { // The gene was in initial set (ergo it can't be in the added genes set)
                    removed_genes[gid] = true; // Add to removed annotations
                    if ( init_annotations[gid].length !== 0 ) {
                        removed_pubs[gid] = annotations[gid];
                    } else {}

                } else { // The gene was being added to the new version

                    delete added_genes[gid];
                    delete added_pubs[gid];

                }

                delete annotations[gid]; // Delete from annotations being passed to new version

            },

            undoGene: function( gid ) {
            // Has functionality that is a bit similar to removeGene, but also works for added and removed annotations 

                if( added_genes[gid] ) { // The gene was not in initial set but had been added
                    delete added_genes[gid];
                    delete added_pubs[gid];
                    delete annotations[gid];

                } else {  // The gene was in initial set and had been removed
                    annotations[gid] = removed_pubs[gid];
                    delete removed_genes[gid]; // Delete from removed genes
                    delete removed_pubs[gid]; // Also delete from removed publications
                } 
                    
            },

            addPublication: function( pubObj, gid ) { 
            // We definitely want this, as it gets called after the user adds a publication using the modal box

                if (annotations[gid]) {
                    annotations[gid].push(pubObj);
                } else {
                    annotations[gid] = [];
                    annotations[gid].push(pubObj);
                }

                if (added_pubs[gid]) {
                    added_pubs[gid].push(pubObj);
                } else {
                    added_pubs[gid] = [];
                    added_pubs[gid].push(pubObj);
                }

            },

            removePublication: function( pubObj, gid, pubstate ) {
                // If the publication was not in initial set, had been added,
                // and user wants to undo the adding:
                if (pubstate === 'added') {
                    added_pubs[gid].splice(added_pubs[gid].indexOf(pubObj), 1);
                    annotations[gid].splice(annotations[gid].indexOf(pubObj), 1);

                    if (added_pubs[gid].length === 0) {
                        delete added_pubs[gid];
                    } else {}

                } else { 
                    if (pubstate === 'removed') {
                        removed_pubs[gid].splice(removed_pubs[gid].indexOf(pubObj), 1);

                        if (removed_pubs[gid].length === 0) {
                            delete removed_pubs[gid];
                        } else {}

                        if (annotations[gid]) {
                            annotations[gid].push(pubObj);
                        } else {
                            annotations[gid] = [];
                            annotations[gid].push(pubObj);
                        }

                    } else { // pubstate must == 'current'
                        if (init_annotations[gid]) { 
                        // If publication *was* in initial annotations, add to removed_pubs
                            if (removed_pubs[gid]) {
                                removed_pubs[gid].push(pubObj);
                            } else {
                                removed_pubs[gid] = [];
                                removed_pubs[gid].push(pubObj);
                            }
                        } else { // Must be in added publications
                            added_pubs[gid].splice(added_pubs[gid].indexOf(pubObj), 1);
                            if (added_pubs[gid].length === 0) {
                                delete added_pubs[gid];
                            } else {}
                        }
                        annotations[gid].splice(annotations[gid].indexOf(pubObj), 1);
                    }
                }

            },

            all: function () {
                return annotations;
            },
            genes: function () {
                return genes;
            },
            added_genes: function () {
                return added_genes;
            },
            added_pubs: function () {
                return added_pubs;
            },
            removed_genes: function () {
                return removed_genes;
            },
            removed_pubs: function () {
                return removed_pubs;
            }
        };
    })

    /**
     * Controller that handles creating a new version.
     */
    .controller( 'NewVersionCtrl', function ( $scope, $state, $stateParams, Versions, GeneSets, Annotations, SearchResults, $rootScope ) {

        $scope.all = Annotations.all();
        $scope.added_genes = Annotations.added_genes();
        $scope.removed_genes = Annotations.removed_genes();
        $scope.added_pubs = Annotations.added_pubs();
        $scope.removed_pubs = Annotations.removed_pubs();
        $scope.genes = Annotations.genes();

        $scope.loadingSearchResults = false;

        $scope.addingPublications = false;
        

        //Fill in existing version stuff
        $scope.version = {};
        $scope.version.full_pubs = true;  // This is so the backend knows we are using 
                                          // the full publication objects w/ db ids
        if ($stateParams.version) {
            // If we are building from an existing version, get it.
            $scope.prior_version = Versions.get({ creator:$stateParams.creator, slug:$stateParams.slug, version:$stateParams.version, xrids_requested:true });
            $scope.prior_version.$promise.then( function () {
                $scope.geneset = $scope.prior_version.geneset;
                $scope.version.geneset = $scope.geneset.resource_uri;
                $scope.version.parent = $scope.prior_version.resource_uri;
                Annotations.init($scope.prior_version.annotations);
                $scope.organism = $scope.prior_version.geneset.organism.resource_uri;
            });
        } else {
            // We're starting with a blank slate.
            $scope.prior_version = null;
            // But we must have a Geneset anyway.
            $scope.geneset = GeneSets.get({ creator:$stateParams.creator, slug:$stateParams.slug });
            $scope.geneset.$promise.then( function() {
                $scope.version.geneset = $scope.geneset.resource_uri;
                $scope.version.parent = null;
                $scope.organism = $scope.geneset.organism.resource_uri;
            });
        }

        //Genes Search
        SearchResults.clear(); //clear any existing search results

        $scope.searchGenes = function() {
            if (!$scope.genesToAdd) { //if the query is empty
                return false;
            }
            $scope.loadingSearchResults = true;
            $rootScope.$broadcast( 'results.loadingSearchResults' );
            qparams = {'query':$scope.genesToAdd.query};
            if ($scope.organism) {
                qparams['organism'] = $scope.organism;
            }
            SearchResults.search(qparams);
        };

        $scope.removeGene = function( gene ) {
            Annotations.removeGene(gene);
        };

        $scope.undoGene = function( gene ) {
            Annotations.undoGene(gene);
        };

        $scope.save = function() {
            $scope.version.annotations = $scope.all;
            Versions.save($scope.version).$promise.then( function( data ) {
                $state.go('use.detail', { creator: data.geneset.creator.username, slug: data.geneset.slug });
            });
        };

        $scope.editPublications = function () {
            $scope.addingPublications = true;    
        };

        $scope.editGenes = function () {
            $scope.addingPublications = false;    
        };

        $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams){ 
            Annotations.clear();
        });

        $scope.$on('results.searchResultsReturned', function() {
            $scope.loadingSearchResults = false;
        });

    })

    /**
     * Controller that handles creating a new version.
     */
    .controller( 'FirstVersionCtrl', function ( $scope, $state, $stateParams, Organisms, GeneSets, Versions, Annotations, SearchResults, $rootScope ) {

        $scope.all = Annotations.all();
        $scope.added_genes = Annotations.added_genes();
        $scope.removed_genes = Annotations.removed_genes();
        $scope.added_pubs = Annotations.added_pubs();
        $scope.removed_pubs = Annotations.removed_pubs();
        $scope.genes = Annotations.genes();

        $scope.addingAnnotations = true;

        $scope.loadingSearchResults = false;

        $scope.addingPublications = false;

        //Fill in new geneset data
        $scope.geneset = {};

        // TODO: get organism
        if ($stateParams.orgslug) {
            $scope.organism = Organisms.get({ slug:$stateParams.orgslug });
            $scope.organism.$promise.then( function() {
                $scope.organism_uri = $scope.organism.objects[0].resource_uri;
                $scope.organism = $scope.organism.objects[0];
                $scope.geneset.organism = $scope.organism_uri;
            });
        }

        $scope.genesToAdd = {};

        //Genes Search
        SearchResults.clear(); //clear any existing search results
        $scope.searchGenes = function() {
            if (!$scope.genesToAdd.query) { //if the query is empty
                return false;
            }
            $scope.loadingSearchResults = true;
            $rootScope.$broadcast( 'results.loadingSearchResults' );
            qparams = {'query':$scope.genesToAdd.query};
            if ($scope.organism_uri) {
                qparams['organism'] = $scope.organism_uri;
            }
            SearchResults.search(qparams);
        };
        
        $scope.removeGene = function( gene ) {
            Annotations.removeGene(gene);
        };

        $scope.undoGene = function( gene ) {
            Annotations.undoGene(gene);
        };

        $scope.editPublications = function () {
            $scope.addingPublications = true;    
        };

        $scope.editGenes = function () {
            $scope.addingPublications = false;    
        };

        $scope.next = function() {
            $scope.addingAnnotations = false;
        };

        $scope.previous = function() {
            $scope.addingAnnotations = true;
        };

        $scope.goToHome = function() {
            $state.go('home');
        };

        $scope.save = function() {

            if ($scope.geneset.title === undefined || $scope.geneset.title ==='') {
                alert('Your collection does not have a title.  Please add a title to be able to create your collection.');
            }
            else {
                GeneSets.save($scope.geneset).$promise.then( function( data ) {
                    $scope.version = {};
                    $scope.version.geneset = data.resource_uri;
                    $scope.version.parent = null;
                    $scope.version.annotations = $scope.all;
                    $scope.version.description = $scope.geneset.abstract;
                    $scope.version.full_pubs = true;  // This is so the backend knows we are using 
                                                      // the full publication objects w/ db ids
                    Versions.save($scope.version).$promise.then( function( data ) {
                        $state.go('use.detail', { creator: data.geneset.creator.username, slug: data.geneset.slug });
                    });
                }, function (error) {
                    alert(error['data']);
                });
            }       

        };

        $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams){ 
            Annotations.clear();
        });

        $scope.$on('results.searchResultsReturned', function() {
            $scope.loadingSearchResults = false;
        });

    })
;