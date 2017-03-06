describe( 'TribeCtrl', function() {
  describe( 'isCurrentUrl', function() {
    var TribeCtrl, $location, $scope;

    beforeEach( module( 'tribe' ) );

    beforeEach( inject( function( $controller, _$location_, $rootScope ) {
      $location = _$location_;
      $scope = $rootScope.$new();
      TribeCtrl = $controller( 'TribeCtrl', { $location: $location, $scope: $scope });
    }));

    
    it( 'should pass a dummy test', inject( function() {
      expect( TribeCtrl ).toBeTruthy();
    }));
   
  });
});
