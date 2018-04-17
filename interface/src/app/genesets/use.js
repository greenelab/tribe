/**
 * Each section of the site has its own module. It probably also has
 * submodules, though this boilerplate is too simple to demonstrate it. Within
 * `src/app/home`, however, could exist several additional folders representing
 * additional modules that would then be listed as dependencies of this one.
 * For example, a `note` section could have the submodules `note.create`,
 * `note.delete`, `note.edit`, etc.
 *
 * Regardless, so long as dependencies are managed correctly, the build process
 * will automatically take take of the rest.
 *
 * The dependencies block here is also where component dependencies should be
 * specified, as shown below.
 */
angular
  .module("tribe.genesets.use", [
    "ui.router.state",
    "ui.bootstrap",
    "tribe.genesets.resource",
    "tribe.genesets.forms",
    "tribe.publications.directives",
    "tribe.genes.directives",
    "tribe.organism",
    "tribe.versions.resource",
    "tribe.genesets.delete",
    "tribe.auth.user",
    "tribe.crossrefdbs.resource"
  ])

  /**
   * Each section or module of the site can also have its own routes. AngularJS
   * will handle ensuring they are all available at run-time, but splitting it
   * this way makes each module more "self-contained".
   */
  .config(function($stateProvider) {
    $stateProvider
      .state("use", {
        url: "/use",
        abstract: true,
        views: {
          main: {
            template: '<div ui-view="main"></div>'
          }
        }
      })
      .state("use.list", {
        url: "/list",
        views: {
          main: {
            controller: "GeneSetListCtrl",
            templateUrl: "genesets/list/list.tpl.html"
          }
        },
        data: {
          pageTitle: "Collections"
        }
      })
      .state("use.detail", {
        url: "/detail/:creator/:slug",
        views: {
          main: {
            controller: "GeneSetDetailCtrl",
            templateUrl: "genesets/detail/detail.tpl.html"
          }
        },
        data: {
          pageTitle: "View Collection"
        }
      })
      .state("use.edit", {
        url: "/edit/:creator/:slug",
        views: {
          main: {
            controller: "GeneSetEditCtrl",
            templateUrl: "genesets/edit/edit.tpl.html"
          }
        },
        data: {
          pageTitle: "Edit Collection"
        }
      })
      .state("use.userGenesets", {
        url: "/my-collections",
        views: {
          main: {
            controller: "GeneSetListCtrl",
            templateUrl: "genesets/list/user-geneset-list.tpl.html"
          }
        },
        data: {
          pageTitle: "My Collections"
        }
      });
  })

  /*
     * GeneSet Search Factory
     * Allows for retreiving for and interacting with search results for genesets.
     */
  .factory("GeneSetSearch", function($rootScope, GeneSets) {
    var genesets = [];
    var query = {};
    var totalResults = 0;
    var offset = 0;
    return {
      getQuery: function() {
        return query;
      },
      getGenesets: function() {
        return genesets;
      },
      clear: function() {
        // Clear the service
        query = {};
        genesets = [];
        $rootScope.$broadcast("genesets.update");
      },
      totalResults: function() {
        return totalResults;
      },
      query: function(searchParams) {
        // Search for genes and add the results to the service
        query = searchParams;
        GeneSets.query(query, function(data) {
          itemsPerPage = data.meta.limit;
          totalResults = data.meta.total_count;
          genesets = data.objects;
          $rootScope.$broadcast("genesets.update");
          $rootScope.$broadcast("genesets.searchResultsReturned");
        });
      }
    };
  })

  /**
   * Controller that handles listing GeneSets.
   */
  .controller("GeneSetListCtrl", function($scope, $state) {
    $scope.itemsPerPage = 10;
  })

  // Directive for SearchBox
  .directive("genesetSearchForm", function(
    OrgList,
    GeneSetSearch,
    UserFactory,
    $rootScope
  ) {
    return {
      controller: [
        "$scope",
        function($scope) {
          $scope.search = { limit: $scope.limit };
          $scope.organisms = OrgList;
          $scope.loadingSearchResults = false;

          if ($scope.mygenesets === true) {
            UserFactory.getPromise().$promise.then(function() {
              $scope.search.creator = UserFactory.getUser()["id"];
            });
          }
          $scope.goSearch = function(search) {
            $rootScope.$broadcast("genesets.loadingSearchResults");
            GeneSetSearch.query(search);
          };

          $scope.$on("genesets.loadingSearchResults", function() {
            $scope.loadingSearchResults = true;
          });

          $scope.$on("genesets.searchResultsReturned", function() {
            $scope.loadingSearchResults = false;
          });
        }
      ],
      replace: true,
      restrict: "E",
      scope: {
        limit: "=limit",
        mygenesets: "="
      },
      templateUrl: "genesets/list/search-form.tpl.html"
    };
  })

  // Directive for table containing search results
  .directive("geneSetTable", function(GeneSetSearch, UserFactory) {
    return {
      controller: [
        "$scope",
        function($scope) {
          UserFactory.getPromise().$promise.then(function() {
            $scope.user = UserFactory.getUser();
          });
          $scope.currentPage = 1;
          $scope.totalResults = 0;
          $scope.genesets = GeneSetSearch.getGenesets();
          $scope.loadingSearchResults = false;
          $scope.maxSize = 10;
        }
      ],
      link: function(scope, element, attr) {
        scope.$on("genesets.update", function() {
          scope.genesets = GeneSetSearch.getGenesets();
          scope.totalResults = GeneSetSearch.totalResults();
        });

        scope.$on("genesets.loadingSearchResults", function() {
          scope.loadingSearchResults = true;
        });

        scope.$on("genesets.searchResultsReturned", function() {
          scope.loadingSearchResults = false;
        });

        // If the user is on a page > 1 and they enter a new search term
        // this will result in double queries. To address this it seems
        // likely that we'd need to re-write and slightly modify the angular-ui
        // bootstrap pager directive.
        scope.$watch("currentPage", function() {
          query = GeneSetSearch.getQuery(); //previous query
          query["limit"] = scope.limit; //set paging info
          query["offset"] = (scope.currentPage - 1) * scope.limit;

          if (scope.mygenesets === true) {
            UserFactory.getPromise().$promise.then(function() {
              query["creator"] = UserFactory.getUser()["id"];
              GeneSetSearch.query(query); //query resource
            });
          } else {
            if ("creator" in query) {
              delete query["creator"];
            }
            GeneSetSearch.query(query); //query resource
          }
        });
      },
      replace: true,
      restrict: "E",
      scope: {
        limit: "=",
        mygenesets: "="
      },
      templateUrl: "genesets/list/search-result-table.tpl.html"
    };
  })

  /**
   * Controller that handles displaying a page for each GeneSet.
   */
  .controller("GeneSetDetailCtrl", function(
    $scope,
    $stateParams,
    $modal,
    $state,
    $location,
    GeneSets,
    UserFactory,
    Versions
  ) {
    // Get Geneset
    var gsParams = {
      creator: $stateParams.creator,
      slug: $stateParams.slug,
      show_versions: true,
      show_team: true
    };

    $scope.geneset = GeneSets.get(gsParams);

    $scope.showVersion = function(chosenVersionHash) {
      var verParams = {
        creator: $stateParams.creator,
        slug: $stateParams.slug,
        version: chosenVersionHash,
        xrids_requested: true
      };
      $scope.chosenVersion = Versions.get(verParams);
    };
    $scope.geneset.$promise.then(function(data) {
      var initialVersion = $scope.geneset.versions[0]["ver_hash"];
      var versionParam = $location.search().version;

      if (versionParam) {
        var matchingVersions = $scope.geneset.versions.filter(function(
          version
        ) {
          return version.ver_hash === versionParam;
        });
        if (matchingVersions.length) {
          initialVersion = versionParam;
        }
      }
      $scope.showVersion(initialVersion); // Load the tip version when page loads
    });

    UserFactory.getPromise().$promise.then(function() {
      $scope.user = UserFactory.getUser();
    });

    $scope.invite = function(email) {
      GeneSets.invite(gsParams, { email: email }, function(data) {
        $scope.geneset = data;
      });
    };

    $scope.openDeleteModal = function() {
      var modalInstance = $modal.open({
        templateUrl: "genesets/delete/deleteGenesetModal.tpl.html",
        controller: "ModalInstanceToDeleteCtrl",
        resolve: {}
      });

      modalInstance.result.then(function(response) {
        if (response === "Delete") {
          GeneSets.rubbish({ id: $scope.geneset.id }).$promise.then(function() {
            $state.go("deleted", {
              //redirect to delete-success page
              creator: $scope.geneset.creator.username,
              slug: $scope.geneset.slug,
              title: $scope.geneset.title
            });
          });
        }
      });
    };

    $scope.openDownloadModal = function(versionHash) {
      var modalInstance = $modal.open({
        templateUrl: "genesets/download/downloadModal.tpl.html",
        controller: [
          "$scope",
          "$modalInstance",
          "CrossrefDBs",
          function($scope, $modalInstance, CrossrefDBs) {
            $scope.versionHash = versionHash;
            $scope.crossRefDbList = ["Symbol"];

            CrossrefDBs.query(function(data) {
              for (var i in data.objects) {
                $scope.crossRefDbList.push(data.objects[i]["name"]);
              }
            });

            $scope.geneIdentifier = "";
            $scope.download = function() {
              $modalInstance.close($scope.geneIdentifier);
            };
            $scope.cancel = function() {
              $modalInstance.dismiss("cancel");
            };
          }
        ],
        resolve: {}
      });

      modalInstance.result.then(function(geneIdentifier) {
        var download_url =
          "http://tribe.greenelab.com/api/v1/version/" +
          $stateParams.creator +
          "/" +
          $stateParams.slug +
          "/" +
          versionHash +
          "/download?xrid=" +
          geneIdentifier;
        window.open(download_url);
      });
    };

    $scope.forkGeneset = function() {
      $state.go("fork", {
        creator: $scope.geneset.creator.username,
        slug: $scope.geneset.slug,
        version: $scope.chosenVersion.ver_hash
      });
    };

    $scope.createNewVersion = function() {
      $state.go("use.newversion", {
        creator: $scope.geneset.creator.username,
        slug: $scope.geneset.slug,
        version: $scope.chosenVersion.ver_hash
      });
    };
  })

  /**
   * Controller that handles editing a GeneSet.
   */
  .controller("GeneSetEditCtrl", function(
    $scope,
    $state,
    $stateParams,
    GeneSets
  ) {
    // Get Geneset
    $scope.geneset = GeneSets.get({
      creator: $stateParams.creator,
      slug: $stateParams.slug
    });
    $scope.geneset.$promise.then(function() {
      $scope.geneset.organism = $scope.geneset.organism.resource_uri; // complete organism is returned, only resource_uri is desired
    });

    $scope.save = function() {
      GeneSets.patch({
        id: $scope.geneset.id,
        title: $scope.geneset.title,
        abstract: $scope.geneset.abstract,
        public: $scope.geneset.public
      }).$promise.then(function(data) {
        $state.go("use.detail", {
          creator: data.creator.username,
          slug: data.slug
        });
      });
    };
  });
