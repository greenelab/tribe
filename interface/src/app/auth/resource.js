/*
 * The resources for interacting with tastypie API
 * The ngResource capabilities encapsulate a lot of the nitty gritty of $http
 * http://docs.angularjs.org/api/ngResource.$resource
 */
angular.module("tribe.auth.resource", ['ngResource', 'ngRoute'])
    .factory('User', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/user/:id', {id: '@id'}, {
            query: {
                method: 'GET',
                isArray: false
            },
            reject: {
                method: 'POST',
                url: '/api/v1/user/reject'
            },
            invite: {
                method: 'POST',
                url: '/api/v1/user/invite'
            },
            login: {
                method: 'POST',
                url: '/api/v1/user/login'
            },
            logout: {
                method: 'POST',
                url: '/api/v1/user/logout'
            }
        });
    }])

;

