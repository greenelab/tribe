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

angular.module('tribe.auth.user', [
    'tribe.auth.resource',
    'ui.router.state',
    'tribe.auth.directives'
    ])

    .config(function ( $stateProvider ) {
        $stateProvider
            .state( 'profile', {
                url: '/profile',
                views: {
                    "main": {
                        controller: 'profileController',
                        templateUrl: 'auth/profile.tpl.html'
                      }
                },
                data: { 
                    pageTitle: 'Profile'
                }
            })
        ;
    })


    .factory( 'UserFactory', function( User ) {
        var promise = false;
        var user = null;

        return {
            getUser: function() { //only call this when the promise completes
                return user;
            },
            getPromise: function() {
                if (!promise) {
                    promise = User.query({}, function( data ) {
                        if (data.meta.total_count !== 0) {
                            user = data.objects[0];
                        }
                    });
                }
                return promise;
            },
            resetPromise: function() { // reset the promise in case we need to check the user again
                promise = false;
            },
            setUser: function( newUser ) { //set the user object to have properties from the passed user
                var member = null;
                for (member in user) {
                    delete user[member]; // delete properties from user
                }
                for (member in newUser) {
                    user[member] = newUser[member];// add properties back to user
                }
            }
        };
    })


    .controller('profileController', function( $scope, UserFactory, User ) {
        $scope.toInvite = {};
        UserFactory.getPromise().$promise.then( function() {
            $scope.user = UserFactory.getUser();
        });
        $scope.invite = function( email ) {
            params = {'email': email };
            User.invite({}, params, function( data ) {
                UserFactory.setUser(data);
                $scope.toInvite = {};
            });
        };
        $scope.reject = function( email ) {
            params = {'email': email };
            User.reject({}, params, function( data ) {
                UserFactory.setUser(data);
            });
        };
    })

;
