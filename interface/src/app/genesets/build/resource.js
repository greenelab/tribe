
angular.module("tribe.genesets.resource", ['ngResource', 'ngRoute'])
    .factory('GeneSets', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/geneset/:id', {id: '@id'}, {
            query: {
                method: 'GET',
                isArray: false
            }
        });
    }])

;
