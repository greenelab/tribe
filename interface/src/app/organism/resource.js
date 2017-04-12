/*
 * The resources for interacting with tastypie API
 * The ngResource capabilities encapsulate a lot of the nitty gritty of $http
 * http://docs.angularjs.org/api/ngResource.$resource
 */
angular.module("tribe.organism.resource", ['ngResource', 'ngRoute'])
    .factory('Organisms', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/organism/:id', {id: '@id'}, {
            query: {
                method: 'GET',
                isArray: false
            }
        });
    }])

;

