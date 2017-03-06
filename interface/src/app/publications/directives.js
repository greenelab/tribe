/*
 * Controllers, services, and directives for searching for
 * and selecting genes.
 */
angular.module('tribe.publications.directives', [
    'tribe.versions.new'
    ])
    
    // Directive for displaying a list of publications
    .directive('pubList', function() {
        return {
            restrict: "E",
            replace: true,
            scope: {
                pubs: '=',
                publength: '='
            },
            templateUrl: 'publications/list.tpl.html'
        };
    })

    // Directive for displaying an individual publication
    .directive('publication', function() {
        return {
            restrict: "E",
            replace: true,
            scope: {
                pub: '=',
                publength: '='
            },
            templateUrl: 'publications/publication.tpl.html'
        };
    })


    .controller( 'RemovablePubCtrl', function ( $scope, Annotations ) {
        $scope.removePublication = function () {
            Annotations.removePublication($scope.pub, $scope.gene, $scope.pubstate);
        };

    })


    // Directive for displaying a list of publications that can be removed
    .directive('removablePubList', function() {
        return {
            restrict: "E",
            replace: true,
            scope: {
                pubs: '=',
                gene: '=',
                publength: '=',
                pubstate: '='
            },
            templateUrl: 'publications/removable-list.tpl.html'
        };
    })

        // Directive for displaying each individual publication, with 
        // the additional functionality of being able to remove the publication
    .directive('removablePublication', function() {
        return {
            restrict: "E",
            replace: true,
            controller: 'RemovablePubCtrl',
            scope: {
                pub: '=',
                gene: '=',
                publength: '=',
                pubstate: '='
            },
            templateUrl: 'publications/removable-publication.tpl.html'
        };
    })

;
