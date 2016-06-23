/*
 * Directives for building a geneset
 */
angular.module('tribe.genesets.build.directives', [

])
    
// Directive for getting started building a collection
    .directive('gettingStartedForm', function( OrgList, UserFactory, User, $state, $modal, $rootScope ) {
        return {
            controller: function ( $scope ) {
                $scope.organisms = OrgList;
                $scope.selectGenes = function( ) {
                    if ($scope.chosenOrgSlug === undefined) {
                        alert('You need to choose an organism to make your collection.');
                    }
                    else { 
                        $state.go('use.firstversion', { orgslug: $scope.chosenOrgSlug });
                    }
                };
            },
            restrict: "E",
            replace: true,
            scope: {
                geneset: '='
            },
            templateUrl: 'genesets/build/getting-started-form.tpl.html'
        };
    })

;