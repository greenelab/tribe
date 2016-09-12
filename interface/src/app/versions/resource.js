angular.module("tribe.versions.resource", ['ngResource', 'ngRoute'])
    .factory('Versions', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/version/:creator/:slug/:version', 
            {creator: '@creator', slug:'@slug', version:'@version'},
            {
                query: {
                    method: 'GET',
                    isArray: false
                }
        });
    }])

;