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
angular.module( 'tribe.build', [
  'ui.router.state',
  'tribe.organism',
  'tribe.genesets.forms',
  'tribe.genesets.resource',
  'tribe.genesets.build.directives'
])

/**
 * Each section or module of the site can also have its own routes. AngularJS
 * will handle ensuring they are all available at run-time, but splitting it
 * this way makes each module more "self-contained".
 */
.config(function ( $stateProvider ) {
  $stateProvider
    .state( 'build', {
      url: '/build',
      views: {
        "main": {
          controller: 'GeneSetBuildCtrl',
          templateUrl: 'genesets/build/build.tpl.html'
        }
      },
      data:{
          pageTitle: 'Build'
      }
    })
    ;
})

/**
 * And we define a controller for our route.
 */
.controller( 'GeneSetBuildCtrl', function ( $scope, $state, GeneSets ) {
    // These next few lines handle the showing of the first and second page of the form to create a Gene Set
    $scope.currentGeneSet = {};
    $scope.clearGeneSet = function() {
        $scope.currentGeneSet = {};
    };
    $scope.saveGeneSet = function() {
        if ($scope.currentGeneSet.title === undefined || $scope.currentGeneSet.title ==='') {
            alert('Your gene set does not have a title.  Please go back and add a title to be able to save your gene set.');
        } // Place a few controls in the interface so that users fill out all of the fields.
        else if ($scope.currentGeneSet.organism === undefined || $scope.currentGeneSet.organism ===''){
            alert('You must choose an organism for your gene set.  Please go back and choose an organism.');
        }
        else {
            GeneSets.save($scope.currentGeneSet).$promise.then( function( data ) {
            $state.go('use.newversion', { creator:data.creator.username, slug:data.slug }); //redirect to the new geneset
            }, function (error) {
                alert(error['data']);
            });
        }       
    };
})

;

