
angular.module("tribe.organism", ["tribe.organism.resource"])
    .service('OrgList', function( Organisms ) {
        orgs = Organisms.query();
        return orgs;
    })

;
