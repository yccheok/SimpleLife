var simpleLifeControllers = angular.module ('simpleLifeControllers', []);

simpleLifeControllers.controller ('IndexCtrl', ['$scope', '$location', '$http',
    function ($scope, $location, $http) {
    }
]);

simpleLifeControllers.controller ('AlbumsListCtrl', ['$scope', '$http', '$location', 'facebook', 
    function ($scope, $http, $location, $facebook) {
        console.log ($facebook.connected);

        if ($facebook.connected) {
            $facebook.api ('me/albums').then (function (result) {
                console.log (result);
                $scope.albums = result.data;
            });
        } else {
            $scope.$on ('fb.auth.authResponseChange', function (event, response) {
                if (response.status === 'connected') {
                    $facebook.api ('me/albums').then (function (result) {
                        console.log (result);
                        $scope.albums = result.data;
                    });
                }
            });
        }
        
        $scope.submit = function () {
            var albums = [];

            angular.forEach (this.albums, function (album) {
                albums.push (album.id);
            });

            console.log (albums);
            $http.post ('albums', albums).success (
                function (data, status, header, config) {
                    console.log ('data posted successfully');

                    $location.path ('/confirm');
                }
            );
        }
            
        $scope.wobble = function () {
            console.log (this);
        }
    }
]);

simpleLifeControllers.controller ('SigninCtrl', ['$rootScope', '$location', '$http',
    function ($rootScope, $location, $http) {
        console.log ($rootScope.user);
        if ($rootScope.user) {
            $location.path ('/');
        }
    }
]).controller ('SignOutCtrl', ['$scope', '$location', '$http', 
    function ($scope, $location, $http) {
        $http.get ('signout').success (function () {
            FB.logout (function (response) {
                $location.path ('/');
            });
        });
    }
]).controller ('ConfirmCtrl', ['$rootScope', '$scope', '$location', '$http', 'RenewToken', '$sce', 
    function ($rootScope, $scope, $location, $http, RenewToken, $sce) {
        $http.get ('/pictures').success (function (info) {
            console.log (info);
        }).error (function (reason) {
            $http.get ('/renew_token?redirect=/#/confirm').success (function (script) {
                console.log (script);
                RenewToken.script = $sce.trustAsHtml (script);
            });
        });
    }
]).controller ('RenewTokenCtrl', function ($scope, RenewToken) {
    $scope.renewToken = RenewToken;
});

