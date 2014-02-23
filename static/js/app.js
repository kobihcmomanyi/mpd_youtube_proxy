var app = angular.module('mpdApp', []);

app.controller('TitleCtrl', function($scope, $http) {
    $scope.title = {};
    $scope.message = {};
    $scope.addTitle = function() {
        $http({
            method: 'POST',
            url: '/title/add',
            data: $scope.title
        }).success(function(data) {
            $scope.message.message = data.message;
            $scope.message.class = data.class;
        });
    };
});