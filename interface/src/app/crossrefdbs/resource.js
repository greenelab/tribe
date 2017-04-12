/*
 * The resources for interacting with tastypie API
 * The ngResource capabilities encapsulate a lot of the nitty gritty of $http
 * http://docs.angularjs.org/api/ngResource.$resource
 */
angular.module("tribe.crossrefdbs.resource", ['ngResource', 'ngRoute'])
    .factory('CrossrefDBs', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/crossrefdb/:id', {id: '@id'}, {
            query: {
                method: 'GET',
                isArray: false
            }
        });
    }]);