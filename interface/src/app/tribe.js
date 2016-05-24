angular.module( 'tribe', [
  'ngCookies',
  'templates-app',
  'templates-common',
  'tribe.home',
  'tribe.demo',
  'tribe.build',
  'tribe.genesets.use',
  'tribe.genesets.fork',
  'tribe.versions.new',
  'tribe.auth.user',

  'ui.router.state',
  'ui.router',
  'ui.route',
  'ui.bootstrap',
  'angularSpinner'
])

.config( function myAppConfig ( $stateProvider, $urlRouterProvider ) {
    $stateProvider
      .state('notAuth', {
          url: '/accounts/login/'
      });
   // $urlRouterProvider.otherwise( '/home' );

})

.run(function($rootScope, $state, $stateParams, $http, $cookies, $location, $window, UserFactory, $modal, User) {

    // States that require users to be logged in:
    var requiredLoginStates = ['build', 'use.edit', 'use.firstversion', 'use.newversion', 'fork', 'profile'];

    String.prototype.startsWith = function(prefix) {
        return this.slice(0, prefix.length) == prefix;
    };

    // To use Django's csrf token and pass it to Tastypie API. For more info
    // on csrf token, see: https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];

    // Allow $state to be used within templates
    // see: https://github.com/angular-ui/ui-router/wiki/Quick-Reference#note-about-using-state-within-a-template
    $rootScope.$state = $state;
    $rootScope.$stateParams = $stateParams;


    $rootScope.$on(
      '$stateChangeStart', function (ev, to, toParams, from, fromParams) {

        if (requiredLoginStates.indexOf(to['name']) > -1) {
            UserFactory.getPromise().$promise.then( function() {

                if (!UserFactory.getUser()) {

                    var modalInstance = $modal.open({
                        templateUrl: 'auth/login-modal-box.tpl.html',
                        controller: [
                          '$scope', '$modalInstance', function($scope,
                                                               $modalInstance) {
                            $scope.message = "You need to sign in to create " +
                                "a collection.";
                            $scope.credentials = {};
                            $scope.login = function () {
                                User.login($scope.credentials)
                                  .$promise.then( function(data) {
                                    if (data['success'] === true) {
                                        $rootScope.$broadcast( 'user.update' );
                                        $modalInstance.close(data['success']);
                                        $window.location.reload();

                                    }
                                });
                            };

                            $scope.cancel = function () {
                                ev.preventDefault();
                                $state.go(from, fromParams);
                                $modalInstance.dismiss('cancel');
                            };
                        }]              
                    });

                    modalInstance.result.then(function (success) {
                        if (success === true) {
                            // continue
                        }
                        else {
                          ev.preventDefault();
                          $state.go(from, fromParams);
                        }
                      } , function () {
                        // This gets called if modal gets dismissed
                        // when user clicks outside modal, etc.
                        ev.preventDefault();
                        $state.go(from, fromParams);
                    });

                }

              else { //continue 
              }

            });
        }
    });

    
    // These next lines tell the interface not to automatically redirect to home if user tries to log in
    // or an external link sent them to one of the geneset pages.

    if ($state['current']['name'] === '') { // Will only redirect if there is no state 
      if (window.location.pathname.startsWith('/accounts') || window.location.pathname.startsWith('/oauth2') || $location.$$path.startsWith('/use') || $location.$$path.startsWith('/build') ) {} // Will not redirect if user wants to log in, or the user is sent from an outside link  TODO - it is pretty hacky, fix 
      else {
          $state.go('home');
      }
    }
})

.controller( 'TribeCtrl', function ( $scope, $location, $modal ) {
  $scope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams){
    if ( angular.isDefined( toState.data.pageTitle ) ) {
      $scope.pageTitle = toState.data.pageTitle + ' | Tribe' ;
    }
  });

})

;

