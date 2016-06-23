
angular.module("tribe.genesets.resource", ['ngResource', 'ngRoute'])
    .factory('GeneSets', ['$resource', '$http', function($resource, $http) {
        return $resource('/api/v1/geneset/:creator/:slug/', { creator: '@creator', slug:'@slug' }, {
            query: {
                url: '/api/v1/geneset/:id',
                method: 'GET',
                isArray: false
            },
            patch: {
                url: '/api/v1/geneset/:id',
                params: { id: '@id' },
                method: 'PATCH'
            },
            invite: {
                method: 'POST',
                url: '/api/v1/geneset/:creator/:slug/invite'
            },
            rubbish: {
                url: '/api/v1/geneset/:id',
                method: 'DELETE',
                params: { id: '@id' }
            }
        });
    }])

;
