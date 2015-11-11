
angular.module( 'tribe.genesets.forms', [
  'ui.router.state',
  'tribe.organism'
])

.directive('genesetEditForm', function( OrgList ) {
    return {
        controller: function ( $scope ) {
            $scope.organisms = OrgList;
        },
        replace: true,
        restrict: "E",
        scope: {
            geneset: '=',
            newset: '='
        },
        templateUrl: 'genesets/build/edit-form.tpl.html'
    };
})

;
