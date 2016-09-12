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
angular.module( 'tribe.demo', [
  'ui.router.state'
])

/**
 * Each section or module of the site can also have its own routes. AngularJS
 * will handle ensuring they are all available at run-time, but splitting it
 * this way makes each module more "self-contained".
 */
.config(function config( $stateProvider ) {
  $stateProvider
    .state( 'democollab', {
        url: '/demo/collaborations',
        views: {
            "main": {
                controller: 'HTMLCtrl',
                templateUrl: 'demo/collab.tpl.html'
            }
        },
        data:{ pageTitle: 'Work with collaborators.' }
    })
    .state( 'demoshare', {
        url: '/demo/share',
        views: {
            "main": {
                controller: 'HTMLCtrl',
                templateUrl: 'demo/share.tpl.html'
            }
        },
        data:{ pageTitle: 'Control your collections.' }
    })
    .state( 'demohistory', {
        url: '/demo/history',
        views: {
            "main": {
                controller: 'HTMLCtrl',
                templateUrl: 'demo/history.tpl.html'
            }
        },
        data:{ pageTitle: 'Keep your history.' }
    })
    .state( 'democode', {
        url: '/demo/code',
        views: {
            "main": {
                controller: 'HTMLCtrl',
                templateUrl: 'demo/code.tpl.html'
            }
        },
        data:{ pageTitle: 'Write simple code.' }
    })
    .state( 'demoids', {
        url: '/demo/speak',
        views: {
            "main": {
                controller: 'HTMLCtrl',
                templateUrl: 'demo/ids.tpl.html'
            }
        },
        data:{ pageTitle: 'Speak one language.' }
    })
    .state( 'demolink', {
        url: '/demo/link',
        views: {
            "main": {
                controller: 'HTMLCtrl',
                templateUrl: 'demo/link.tpl.html'
            }
        },
        data:{ pageTitle: 'Link with Tribe.' }
    })
  ;
})

/**
 * And of course we define a controller for our route.
 */
.controller( 'HTMLCtrl', function ( $scope ) {
})

;