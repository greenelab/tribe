/*
 * The resources for interacting with tastypie API
 * The ngResource capabilities encapsulate a lot of the nitty gritty of $http
 * http://docs.angularjs.org/api/ngResource.$resource
 */
angular.module("tribe.gene.resource", ['ngResource', 'ngRoute'])
    .factory('Genes', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/gene/:id', {id: '@id'}, {
            search: {
                url: '/api/v1/gene/search',
                method: 'GET',
                isArray: true
            }
        });
    }]);
