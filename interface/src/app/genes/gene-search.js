/*
 * Controllers, services, and directives for searching for
 * and selecting genes.
 */
angular.module('tribe.gene.search', [
    'ui.router.state',
    'tribe.gene.resource',
    'tribe.versions.new'
    ])
    
    .factory( 'SearchResults', function( $rootScope, Genes ) {
        var queries = [];
        var searchResults = {};
        return {
            getQueries: function () {
                return queries;
            },
            getQueryResults: function ( query ) {
                return searchResults[query];
            },
            getSearchResults: function () {
                return searchResults;
            },
            remove: function ( query ) { // Remove a query and its associated result
                queries = queries.filter(function(el) { return el != query; });
                delete searchResults[ query ];
                $rootScope.$broadcast( 'results.update' );
            },
            clear: function () { // Clear the service
                queries = [];
                searchResults = {};
                $rootScope.$broadcast( 'results.update' );
            },
            moreQuery: function( query ) { // Get new page of results for the query
                return true;
            },
            size: function() {
                return queries.length;
            },
            search: function ( qparams ) { // Search for genes and add the results to the service
                Genes.search(qparams, function(data) {
                    var previousQueries = queries.length;
                    for (var i = 0; i < data.length; i++) {
                        query = data[i].search;
                        if (!searchResults[ query ]) { //if search term didn't already exist
                            searchResults[ query ] = data[i]; //add it to the results
                            queries.push(query);// add to the list of queries
                        }
                    }
                    if (previousQueries != queries.length) {
                        $rootScope.$broadcast( 'results.update' );
                    }
                    $rootScope.$broadcast( 'results.searchResultsReturned' );
                });
            }
        };
    })

   
    // Directive for table containing search results
    .directive('searchResultTable', function( SearchResults, Annotations ) {
        return {
            controller: ['$scope', 'SearchResults', 'Annotations',  function($scope, SearchResults, Annotations) {
                $scope.currentPage = 1;
                $scope.itemsPerPage = 10;
                $scope.totalResults = 0;
                $scope.maxSize = 10;
                $scope.resultsForPage = [];
                $scope.searchResults = SearchResults.getSearchResults();
                $scope.loadingSearchResults = false;

                $scope.addAllNonAmbiguous = function() {  
                // Function to automatically add all genes that only have one search result
                    var searchResults = SearchResults.getSearchResults();
                    for (var key in searchResults) {
                        var results = searchResults[key];
                        if (results['found'].length <= 1) {
                            if (results['found'][0]) {
                                var gene = results['found'][0];
                                Annotations.addGene(gene);
                                SearchResults.remove(key);
                            }
                        }            
                    }
                };


                $scope.removeNotFound = function() {  
                // Function to get rid of all the queries that returned no results.
                    var searchResults = SearchResults.getSearchResults();
                    for (var key in searchResults) {
                        var results = searchResults[key];
                        if (results['found'].length === 0) {
                            SearchResults.remove(key);
                        }            
                    }
                };


            }],
            link: function(scope, element, attr) {
                scope.$on('results.update', function() {
                    scope.totalResults = SearchResults.size();
                    var begin = ((scope.currentPage-1)*scope.itemsPerPage), end = begin + scope.itemsPerPage;
                    scope.resultsForPage = SearchResults.getQueries().slice(begin, end);
                });

                scope.$on('results.loadingSearchResults', function() {
                    scope.loadingSearchResults = true;
                });

                scope.$on('results.searchResultsReturned', function() {
                    scope.loadingSearchResults = false;
                });
        
                //Watch for page changes and update
                scope.$watch('currentPage', function() {
                    var begin = ((scope.currentPage-1)*scope.itemsPerPage), end = begin + scope.itemsPerPage;
                    scope.resultsForPage = SearchResults.getQueries().slice(begin, end);
                });
            },
            replace: true,
            restrict: "E",
            scope: true,
            templateUrl: 'genes/search-result-table.tpl.html'
        };
    })
    
    // Directive for button where user does not find a result
    // Should remove entire row from list
    .directive('noResultButton', function( SearchResults ) {
        return {
            link: function(scope, element, attr) {
                element.bind( "click", function() {
                    // Because this results in data being updated
                    // and isn't using ng-* listeners we need to
                    // wrap things in $apply()
                    // http://jimhoskins.com/2012/12/17/angularjs-and-apply.html
                    scope.$apply( function() { 
                        SearchResults.remove( scope.query );
                    });
                });
            },
            replace: true,
            restrict: "E",
            scope: {
                query: '@'
            },
            templateUrl: 'genes/no-result-button.tpl.html'
        };
    })

    // Directive for button with a gene, should add gene
    // and remove entire row from list
    .directive('geneResultButton', function( Annotations, SearchResults ) {
        return {
            restrict: "E",
            link: function(scope, element, attr) {
                element.bind( "click", function() {
                    scope.$apply( function() {
                        Annotations.addGene( scope.gene );
                        SearchResults.remove( scope.query );
                    });
                });
            },
            replace: true,
            templateUrl: 'genes/gene-result-button.tpl.html'
        };
    })
    
    // Directive for button to get more options, should get
    // next page of search results for this query from the server
    .directive('moreResultButton', function( SearchResults ) {
        return {

            link: function(scope, element, attr) {

                element.bind( "click", function() {
                    scope.page = scope.pageDict.page;
                    scope.page = scope.page + 1;
                    scope.$apply( function() {
                        scope.pageDict.page = scope.page;
                        scope.updatePage(scope.page);
                    });
                });
            },
            replace: true,
            restrict: "E",
            scope: false, 
            templateUrl: 'genes/more-result-button.tpl.html'
        };
    })

    // Directive for button to get previous search results 
    .directive('previousResultButton', function( SearchResults ) {
        return {

            link: function(scope, element, attr) {

                element.bind( "click", function() {
                    scope.page = scope.pageDict.page;
                    scope.page = scope.page - 1;
                    scope.$apply( function() {
                        scope.pageDict.page = scope.page;
                        scope.updatePage(scope.page);
                    });
                });
            },
            replace: true,
            restrict: "E",
            scope: false, 
            templateUrl: 'genes/previous-result-button.tpl.html'
        };
    })
    
    // Directive for search buttonset, has buttons for handling
    // search results
    .directive('searchButtonset', function( SearchResults ) {
        return {
            controller: function( $scope ) {
                $scope.pageDict = {page: 1};
                $scope.results = SearchResults.getQueryResults( $scope.query );
                $scope.found = $scope.results.found;
                var begin, end;
                $scope.updatePage = function(page) {
                    begin = ((page-1)*3), end=begin+3;
                    $scope.pageGenes = $scope.found.slice(begin, end);
                    $scope.additionalPages = (end < $scope.found.length);// Boolean, telling whether or not there is (are) any additional result page(s)
                    $scope.previousPages = (begin > 0);// Boolean, telling whether or not there is (are) any previous page(s)

                };
                $scope.updatePage($scope.pageDict.page);

            },

            restrict: "E",
            replace: true,
            scope: {
                query: '='
            },
            templateUrl: 'genes/search-buttonset.tpl.html'
        };
    })

;
