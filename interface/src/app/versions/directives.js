/*
 * Directives for listing annotations in versions.
 */

angular.module('tribe.versions.directives', [

    ])

    .controller( 'ModalPubCtrl', function ( $scope, $modal, Publication, Annotations ) {

        $scope.newPub = {};

        $scope.open = function (geneID) {

            var modalInstance = $modal.open({
                templateUrl: 'versions/modalPubBox.tpl.html',
                controller: 'ModalInstanceCtrl',
                resolve: {
                }               
            });

            modalInstance.result.then(function (pubMedID) {
                $scope.pub = Publication.get({ pmid:pubMedID, search_pmid:pubMedID });
                $scope.pub.$promise.then( function() {
                    $scope.newPubObj = $scope.pub;
                    // geneID was passed as parameter to this open() function
                    Annotations.addPublication($scope.newPubObj, geneID);
                });
            });
        };
    }) 


    .controller( 'ModalInstanceCtrl', function ( $scope, $modalInstance ) {
        $scope.entered = {};
        $scope.add = function () {
            $modalInstance.close($scope.entered.pmid);
        };
        $scope.cancel = function () {
            $modalInstance.dismiss('cancel');
        };
    })

    .directive( 'genericAnnotationList', function( ) {
        return {
            controller: ['$scope', function( $scope ) {
                $scope.pubLength = "short";
            }],
            replace: true,
            restrict: "E",
            scope: {
                annotations: '=',
                editable: '=',
                removeGene: '=',
                genes: '='
            },
            templateUrl: 'versions/generic-annotation-list.tpl.html'
        };
    })
    .directive( 'extendedAnnotationList', function( ) {
        return {
            replace: true,
            restrict: "E",
            controller: 'ModalPubCtrl',
            scope: {
                annotations: '=',
                removeGene: '=',
                genes: '=',
                pubstate: '='

            },
            templateUrl: 'versions/extended-annotation-list.tpl.html'
        };
    })

	.directive( 'addedRemovedAnnotationList', function( Annotations ) {
	// We want a separate directive for added and removed annotations, as we
	// want to include removed publications as well
        return {
			controller: ['$scope', function( $scope ) {
				$scope.pubLength = "short";
                $scope.genesEdited = false;
                $scope.publicationsEdited = false;
                $scope.undoGene = function (gid) {
                    Annotations.undoGene(gid);
                };

			}],
            replace: true,
            restrict: "E",
            scope: {
                editedGenes: '=',
                editedPubs: '=',
                genes: '=',
                pubstate: '='

            },
            link: function( scope, element, attrs) {

                scope.$watch('editedGenes', function () {
                    if (_.isEmpty(scope.editedGenes)) {
                        scope.genesEdited = false;
                    } else {
                        scope.genesEdited = true;
                    }
                }, true); // The 'true' parameter at the end of this function is very important, else changes will not be detected

                scope.$watch('editedPubs', function () {
                    if (_.isEmpty(scope.editedPubs)) {
                        scope.publicationsEdited = false;
                    } else {
                        scope.publicationsEdited = true;
                    }
                }, true); // The 'true' parameter at the end of this function is very important, else changes will not be detected

            },
            templateUrl: 'versions/added-removed-annotation-list.tpl.html'
        };
    })

;