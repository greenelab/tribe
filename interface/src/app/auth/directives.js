angular.module('tribe.auth.directives', [

])

    .directive('loginButton', function(UserFactory) { 
        return {
            controller: ['$scope', 'UserFactory', 'User', '$modal', function( $scope, UserFactory, User, $modal ) {
                $scope.userObj = false;

                UserFactory.getPromise().$promise.then( function() {
                    $scope.userObj = UserFactory.getUser();
                });

                $scope.openLoginModal = function() {

                    var modalInstance = $modal.open({
                        templateUrl: 'auth/login-modal-box.tpl.html',
                        controller: 'LoginModalCtrl',
                        resolve: {
                        }               
                    });

                    modalInstance.result.then(function (credentials) {
                        User.login(credentials);
                    });
                };
            }],
            link: function(scope, element, attr) {
                scope.$on('user.update', function() {
                    UserFactory.resetPromise();
                    UserFactory.getPromise().$promise.then( function() {
                        scope.userObj = UserFactory.getUser();
                    });
                });
            },
            replace: true,
            restrict: "E",
            templateUrl: 'auth/login-button.tpl.html'
        };
    })


    .controller( 'LoginModalCtrl', function ( $scope, $modalInstance ) {
        $scope.credentials = {};
        $scope.login = function () {
            $modalInstance.close($scope.credentials);
        };

        $scope.cancel = function () {
            $modalInstance.dismiss('cancel');
        };
    })


    .directive('temporaryAcctButton', function(UserFactory) { 
        return {
            controller: ['$scope', 'UserFactory', function( $scope, UserFactory ) {
                $scope.userObj = false;
                UserFactory.getPromise().$promise.then( function() {
                    $scope.userObj = UserFactory.getUser();
                });
            }],
            replace: true,
            restrict: "E",
            templateUrl: 'auth/temporary-acct-button.tpl.html'
        };
    })


    .directive('profileButton', function(UserFactory) { 
        return {
            controller: ['$scope', 'UserFactory', 'User', '$modal', function( $scope, UserFactory, User, $modal ) {
                $scope.userObj = false;
                UserFactory.getPromise().$promise.then( function() {
                    $scope.userObj = UserFactory.getUser();
                    if ($scope.userObj) {
                      $scope.username = $scope.userObj.username;
                      if ($scope.username.startsWith('TemporaryUser')) {
                          $scope.username = 'Temporary User';
                      }
                    }
                });

                $scope.openLogoutModal = function() {

                    var modalInstance = $modal.open({
                        templateUrl: 'auth/logout-modal-box.tpl.html',
                        controller: 'LogoutModalCtrl',
                        resolve: {
                        }               
                    });

                    modalInstance.result.then(function (confirmation) {
                        if (confirmation === true) {
                            User.logout();
                        }
                    });
                };
            }],
            link: function(scope, element, attr) {
                scope.$on('user.update', function() {
                    UserFactory.resetPromise();
                    UserFactory.getPromise().$promise.then( function() {
                        scope.userObj = UserFactory.getUser();
                        if (scope.userObj) {
                            scope.username = scope.userObj.username;
                            if (scope.username.startsWith('TemporaryUser')) {
                                scope.username = 'Temporary User';
                            }
                        }
                    });
                });
            },
            replace: true,
            restrict: "E",
            templateUrl: 'auth/profile-button.tpl.html'
        };
    })


    .controller( 'LogoutModalCtrl', function ( $scope, $modalInstance ) {
        $scope.confirmation = false;
        $scope.logout = function () {
            $scope.confirmation = true;
            $modalInstance.close($scope.confirmation);
        };

        $scope.cancel = function () {
            $modalInstance.dismiss('cancel');
        };
    })

;