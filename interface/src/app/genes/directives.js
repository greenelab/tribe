/*
 * Directives for searching for
 * and selecting genes.
 */
angular.module('tribe.genes.directives', [])
    
// Directive for displaying gene object
.directive('geneItem', function() {
  return {
    restrict: "E",
    replace: true,
    scope: {
      gene: '='
    },
    templateUrl: 'genes/item.tpl.html'
  };
})

.directive('geneboxPopup', function () {
  return {
    restrict: 'EA',
    replace: true,
    scope: {
      content: '@',
      placement: '@',
      animation: '&',
      isOpen: '&',
      manualHide: '&'
    },
    link: function(scope) {
      gene = JSON.parse(scope.content);
      scope.title = gene['standard_name'];
      scope.description = gene['description'];
      scope.xrids = gene['xrids'];
      scope.entrezid = gene['entrezid'];
      scope.aliases = gene['aliases'];
    },
    templateUrl: 'genes/gene-box-popup.tpl.html'
  };
})

.directive('genebox', ['$tooltip', function ($tooltip) {
  return $tooltip('genebox', 'popover', 'focus', {
    useContentExp: true
  });
}])

;
