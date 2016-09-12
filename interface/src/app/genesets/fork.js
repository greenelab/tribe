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
angular.module( 'tribe.genesets.fork', [
  'ui.router.state',
  'tribe.versions.resource',
  'tribe.genesets.forms'
])

/**
 * Each section or module of the site can also have its own routes. AngularJS
 0* will handle ensuring they are all available at run-time, but splitting it
 * this way makes each module more "self-contained".
 */
    .config(function ( $stateProvider ) {
        $stateProvider
            .state( 'fork', {
                url: '/fork/:creator/:slug/:version',
                views: {
                    "main": {
                        controller: 'GeneSetForkCtrl',
                        templateUrl: 'genesets/fork/fork.tpl.html'
                    }
                },
                data: {
                    pageTitle: 'Fork'
                }
            })
        ;
    })

    /**
     * Controller that handles forking GeneSets.
     */
    .controller( 'GeneSetForkCtrl', function ( $state, $scope, $stateParams, Versions, GeneSets ) {
        $scope.version = Versions.get({creator:$stateParams.creator, slug:$stateParams.slug, version:$stateParams.version});
        $scope.version.$promise.then(function() { // When things return, create a new geneset object
            $scope.newGeneset = {};

            $scope.newGeneset.title = "Fork of " + $scope.version.geneset.title +
                " at version " + $scope.version.ver_hash.slice(0, 12);

            $scope.newGeneset.organism = $scope.version.geneset.organism.resource_uri;
            $scope.newGeneset.abstr = $scope.version.geneset.abstr;
            $scope.newGeneset.public = $scope.version.geneset.public;
            $scope.newGeneset.fork_of = $scope.version.geneset.resource_uri;
            $scope.newGeneset.fork_version = $scope.version.ver_hash;

        });

        $scope.fork = function() { // Save the new geneset object
            GeneSets.save($scope.newGeneset).$promise.then(
                function( data ) {
                    $state.go('use.detail', {creator:data.creator.username,
                                             slug: data.slug});
                },
                function ( error ) {
                    alert(error['data']);
                });
        };

    })

;
