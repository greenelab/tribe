
angular.module("tribe.publications.resource", ['ngResource', 'ngRoute'])
    .factory('Publication', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/publication/:pmid', {pmid: '@pmid'}, {
            query: {
                method: 'GET',
                isArray: false
            }
        });
    }])

;
