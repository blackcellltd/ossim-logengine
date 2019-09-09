'use strict';


var app = angular.module('bcloggerApp', ['ui.bootstrap', 'chart.js']);


app.directive('convertToNumber', function () {
    return {
        require: 'ngModel',
        link: function (scope, element, attrs, ngModel) {
            ngModel.$parsers.push(function (val) {
                return parseInt(val, 10);
            });
            ngModel.$formatters.push(function (val) {
                return '' + val;
            });
        }
    };
});

app.controller("StatsCtrl", ['$scope', '$http', '$timeout', function ($scope, $http) {
    $scope.barLabels = [];
    $scope.barSeries = ['Number of logs'];
    $scope.activePlugins = [];
    $scope.resolutions = [
        {value: "hours", name: "Hours"},
        {value: "days", name: "Days"},
        {value: "weeks", name: "Weeks"},
        {value: "months", name: "Months"}
    ];

    $scope.barData = [
        []
    ];

    $scope.pieData = [];
    $scope.pieLabels = [];

    $scope.count = 8;
    $scope.resolution = "hours";
    $scope.offset = 0;

    $scope.formatDate = function (datestring) {

        function addZero(i) {
            if (i < 10) {
                i = "0" + i;
            }
            return i;
        }

        var date = new Date(datestring);
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();
        var hour = date.getHours();
        var minutes = addZero(date.getMinutes());
        var seconds = addZero(date.getSeconds());

        return year + "." + month + "." + day + ". " + hour + ":" + minutes + ":" + seconds;
    };

    $scope.loadBarGraph = function () {
        var payload = {
            count: $scope.count,
            resolution: $scope.resolution,
            offset: $scope.offset,
            path: 'logarchive/statsBarGraph'
        };

        $http({
            method: 'POST',
            url: 'index.php',
            data: payload
        })
            .success(function (data, status) {
                if (status == 200) {
                    var i = 0;
                    $scope.barData[0] = data.requested;
                    $scope.barLabels = [];
                    var len = $scope.barData[0].length;
                    for (i = 0; i < len; ++i) {
                        // mulitline label
                        var label = $scope.formatDate(data.labels[2 * i]) + " " + $scope.formatDate(data.labels[2 * i + 1]);
                        label = label.split(/\s/g);
                        $scope.barLabels[i] = label;
                    }
                }
                else {
                }
            });
    };

    $scope.loadPieChart = function () {
        var payload = {
            path: 'logarchive/activePlugins'
        };
        $http({
            method: 'POST',
            url: 'index.php',
            data: payload
        }).success(function (data, status) {
            if (status == 200) {
                $scope.activePlugins = data.plugins;
                var payload = {
                    path: 'logarchive/pluginsPieChart'
                };

                $http({
                    method: 'POST',
                    url: 'index.php',
                    data: payload
                })
                    .success(function (data, status) {
                        if (status == 200) {
                            var len = data.plugins_with_percentage.length;
                            for (var i = 0; i < len; ++i) {
                                try {
                                    $scope.pieData[i] = data.plugins_with_percentage[i].count;
                                    var elem = $scope.activePlugins.filter(function (item) {
                                        return item.id == data.plugins_with_percentage[i]._id
                                    })[0];
                                    $scope.pieLabels[i] = elem.name + " on " + elem.ossim_name;
                                } catch (e) {
                                    //bad data from DB (plugin_id is null)
                                }
                            }

                        }
                        else {
                        }
                    });
            }
            else {
            }
        });
    };

    $scope.load = function () {
        $scope.loadBarGraph();
        $scope.loadPieChart();
    };

    $scope.load();
}]);

app.controller("resultsController", ['$scope', '$http', '$timeout', '$window', '$uibModal', function ($scope, $http, $timeout, $window, $uibModal) {
    $scope.results = []; //contains the results of query
    $scope.showFilter = {}; // filter + boolean (shown or not)
    $scope.originalResultLength = 0; //length of full query(needed for pagination)
    $scope.filters_backup = {}; //filter backup for restoring the initial state (everything shown)
    $scope.currentFilter = {}; //contains the currently selected filter
    $scope.filters = {};
    $scope.filtertypes = [
        {name: "username", hrName: "Username", placeholder: "Username"},
        {name: "ip_src", hrName: "Source IP", placeholder: "aaa.bbb.ccc.ddd"},
        {name: "ip_dst", hrName: "Destination IP", placeholder: "aaa.bbb.ccc.ddd"},
        {name: "src_hostname", hrName: "Source Hostname", placeholder: "hostname"},
        {name: "dst_hostname", hrName: "Destination Hostname", placeholder: "hostname"},
        {name: "layer4_sport", hrName: "Source Port", placeholder: "12345"},
        {name: "layer4_dport", hrName: "Destination Port", placeholder: "aaaaaa"},
        {name: "src_mac", hrName: "Source MAC", placeholder: "AA:BB:CC:DD:EE:FF"},
        {name: "dst_mac", hrName: "Destination MAC", placeholder: "AA:BB:CC:DD:EE:FF"},
        {name: "id", hrName: "ID", placeholder: "ID"}
    ];
    $scope.advancedFilters = false;
    $scope.advancedFiltertypes = [
        {name: "userdata1", hrName: "Userdata 1", placeholder: "Userdata"},
        {name: "userdata2", hrName: "Userdata 2", placeholder: "Userdata"},
        {name: "userdata3", hrName: "Userdata 3", placeholder: "Userdata"},
        {name: "userdata4", hrName: "Userdata 4", placeholder: "Userdata"},
        {name: "userdata5", hrName: "Userdata 5", placeholder: "Userdata"},
        {name: "userdata6", hrName: "Userdata 6", placeholder: "Userdata"},
        {name: "userdata7", hrName: "Userdata 7", placeholder: "Userdata"},
        {name: "userdata8", hrName: "Userdata 8", placeholder: "Userdata"},
        {name: "userdata9", hrName: "Userdata 9", placeholder: "Userdata"}
    ];
    $scope.currentPage = 1;
    $scope.maxPageSize = 10;
    $scope.numPerPage = 10;
    $scope.numPerPages = [10, 25, 50, 100]; // items shown on a page
    $scope.filters2send = {}; //filters sent in http request
    $scope.numberofLogs = 0;
    $scope.activePlugins = [];
    $scope.sids = [];
    $scope.withSid = [];

    $scope.sidToggleChanged = function (index, toggled) {
        if (!toggled)
            delete $scope.filters['plugin_id']['$or'][index]['plugin_sid'];
    };

    //Format date to YYYY.MM.DD. HH:MM:SS
    $scope.formatDate = function (datestring) {

        function addZero(i) {
            if (i < 10) {
                i = "0" + i;
            }
            return i;
        }

        var date = new Date(datestring);
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();
        var hour = date.getHours();
        var minutes = addZero(date.getMinutes());
        var seconds = addZero(date.getSeconds());

        return year + "." + month + "." + day + ". " + hour + ":" + minutes + ":" + seconds;
    };

    $scope.identity = function (x) {
        return x;
    };

    $scope.getPluginName = function (pluginid, ossimid) {
        return $scope.activePlugins.filter(function (item) {
            return item.id == pluginid && item.ossim_id == ossimid;
        })[0].name;
    };

    $scope.filterSid = function (crit) {
        //{id: Number(filters['plugin_id']['$or'][$index]['plugin_id'].split('_')[0]), ossim_id: filters['plugin_id']['$or'][$index]['plugin_id'].split('_')[1]}
        return function (item) {
            return item.id == crit.split('_')[0] && item.ossim_id == crit.split('_')[1];
        }
    };

    /**
     * @return {string}
     */
    $scope.Plugin = function (pid, oid) {
        return pid + '_' + oid;
    };

    $scope.defaultFields = [
        {name: 'Timestamp', fieldName: 'timestamp', formatter: $scope.formatDate},
        {name: 'Source IP', fieldName: 'ip_src', formatter: $scope.identity},
        {name: 'Destination IP', fieldName: 'ip_dst', formatter: $scope.identity},
        {name: 'Source Hostname', fieldName: 'src_hostname', formatter: $scope.identity},
        {name: 'Data payload', fieldName: 'data_payload', formatter: $scope.identity},
        {name: 'Ossim name', fieldName: 'ossim_name', formatter: $scope.identity}
    ];

    $scope.optionalFields = [
        {name: 'Layer4 source port', fieldName: 'layer4_sport', formatter: $scope.identity},
        {name: 'Layer4 destination port', fieldName: 'layer4_dport', formatter: $scope.identity},
        {name: 'Username', fieldName: 'username', formatter: $scope.identity},
        {name: 'Password', fieldName: 'password', formatter: $scope.identity},
        {name: 'Source Host', fieldName: 'src_host', formatter: $scope.identity},
        {name: 'Source Net', fieldName: 'src_net', formatter: $scope.identity},
        {name: 'Source MAC', fieldName: 'src_mac', formatter: $scope.identity},
        {name: 'Destination Host', fieldName: 'dst_host', formatter: $scope.identity},
        {name: 'Destination Hostname', fieldName: 'dst_hostname', formatter: $scope.identity},
        {name: 'Destination Net', fieldName: 'dst_net', formatter: $scope.identity},
        {name: 'Destination MAC', fieldName: 'dst_mac', formatter: $scope.identity},
        {name: 'Filename', fieldName: 'filename', formatter: $scope.identity},
        {name: 'Binary data', fieldName: 'binary_data', formatter: $scope.identity}
    ];

    $scope.advancedOptionalFields = [
        {name: "Userdata 1", fieldName: "userdata1", formatter: $scope.identity},
        {name: "Userdata 2", fieldName: "userdata2", formatter: $scope.identity},
        {name: "Userdata 3", fieldName: "userdata3", formatter: $scope.identity},
        {name: "Userdata 4", fieldName: "userdata4", formatter: $scope.identity},
        {name: "Userdata 5", fieldName: "userdata5", formatter: $scope.identity},
        {name: "Userdata 6", fieldName: "userdata6", formatter: $scope.identity},
        {name: "Userdata 7", fieldName: "userdata7", formatter: $scope.identity},
        {name: "Userdata 8", fieldName: "userdata8", formatter: $scope.identity},
        {name: "Userdata 9", fieldName: "userdata9", formatter: $scope.identity}
    ];

    $scope.hiddenFields = [
        {name: 'Ip proto', fieldName: 'ip_proto'},
        {name: 'Timezone', fieldName: 'tzone'},
        {name: '_ID', fieldName: '_id'},
        {name: 'CTX: ', fieldName: 'ctx'},
        {name: 'ID', fieldName: 'id'},
        {name: 'Ossim asset source', fieldName: 'ossim_asset_src'},
        {name: 'Ossim asset destination', fieldName: 'ossim_asset_dst'},
        {name: 'Ossim correlation', fieldName: 'ossim_correlation'},
        {name: 'Ossim priority', fieldName: 'ossim_priority'},
        {name: 'Ossim reliability', fieldName: 'ossim_reliability'},
        {name: 'Ossim risk a', fieldName: 'ossim_risk_a'},
        {name: 'Ossim risk c', fieldName: 'ossim_risk_c'},
        {name: 'Device ID', fieldName: 'device_id'}
    ];

    $scope.getAccordionFields = function () {
        var more = $scope.advancedFilters ? $scope.advancedOptionalFields : [];
        return [].concat($scope.optionalFields, more);
    };

    $scope.setNumPerPage = function (size) {
        $scope.numPerPage = size;
        $scope.pageChangedOrSearch(true);
    };

    //This function gives us a query without filter, on first load, everything is in the list
    $window.onload = function () {
        var payload = {
            path: 'logarchive/activePlugins'
        };
        $http({
            method: 'POST',
            url: 'index.php',
            data: payload
        }).success(function (data, status) {
            if (status == 200) {
                $scope.activePlugins = data.plugins;
                $scope.sids = data.sids;
            }
            else {
            }
        });
        $scope.pageChangedOrSearch(true);
    };

    //Pagination help function: setting the page number
    $scope.setPage = function (pageNo) {
        $scope.currentPage = pageNo;
    };

    //Generates an html or pdf report
    $scope.generateReport = function (mode) {
        if ($scope.originalResultLength > 5000) {
            return;
        }

        $scope.filters2send = {$and: []};
        angular.forEach($scope.filters, function (filter) {
            if (filter['$or'][0].plugin_id == undefined) {
                $scope.filters2send['$and'].push(filter);
            }
            else {
                var filter2push = {};
                filter2push['$or'] = [];
                for (var i = 0; i < filter['$or'].length; ++i) {
                    filter2push['$or'][i] = {};
                    filter2push['$or'][i].plugin_id = Number(filter['$or'][i].plugin_id.split('_')[0]);
                    filter2push['$or'][i].ossim_id = filter['$or'][i].plugin_id.split('_')[1];
                    if (filter['$or'][i].plugin_sid != undefined)
                        filter2push['$or'][i].plugin_sid = filter['$or'][i].plugin_sid;
                }
                $scope.filters2send['$and'].push(filter2push);
            }
        });
        if (Object.keys($scope.filters).length === 0)
            $scope.filters2send = {};
        var payload = {
            filter: $scope.filters2send,
            currentPage: 1,
            pageSize: $scope.numPerPage,
            path: 'logarchive/json',
            report: mode
        };
        $http({
                method: 'POST',
                url: 'index.php',
                data: payload,
                responseType: 'arraybuffer'
            }
        ).then(function (response) {
            var headers = response.headers();
            var blob = new Blob([response.data], {type: headers['content-type']});
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = "Report";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });

    };

    //Pagination help function: if page changes, we make a new query
    //Search function, sends an http request with the filters and pagination information, it always resets the current page
    $scope.pageChangedOrSearch = function (isSearch) {
        $scope.filters2send = {$and: []};
        angular.forEach($scope.filters, function (filter) {
            if (filter['$or'][0].plugin_id == undefined) {
                $scope.filters2send['$and'].push(filter);
            }
            else {
                var filter2push = {};
                filter2push['$or'] = [];
                for (var i = 0; i < filter['$or'].length; ++i) {
                    filter2push['$or'][i] = {};
                    filter2push['$or'][i].plugin_id = Number(filter['$or'][i].plugin_id.split('_')[0]);
                    filter2push['$or'][i].ossim_id = filter['$or'][i].plugin_id.split('_')[1];
                    if (filter['$or'][i].plugin_sid != undefined)
                        filter2push['$or'][i].plugin_sid = filter['$or'][i].plugin_sid;
                }
                $scope.filters2send['$and'].push(filter2push);
            }
        });
        if (Object.keys($scope.filters).length === 0)
            $scope.filters2send = {};
        var payload = {
            filter: $scope.filters2send,
            currentPage: isSearch ? 1 : $scope.currentPage,
            pageSize: $scope.numPerPage,
            path: 'logarchive/json'
        };

        $http({
            method: 'POST',
            url: 'index.php',
            data: payload
        })
            .success(function (data, status) {
                if (status == 200) {
                    $scope.results = data.splice(1);
                    $scope.originalResultLength = data[0]; //first item is the number of items
                }
                else {
                    $scope.showError("Unknown error", data);
                }
            });

        payload = {
            path: 'logarchive/count'
        };
        $http({
            method: 'POST',
            url: 'index.php',
            data: payload
        })
            .success(function (data, status) {
                if (status == 200) {
                    $scope.numberofLogs = data.count;
                }
                else {
                }
            });
    };

    //Filter help function: adds selected filter, by default it's empty
    $scope.addFilter = function (filter) {
        if (!$scope.filters[filter])
            $scope.filters[filter] = {$or: []};
        var obj = {};
        obj[filter] = '';
        $scope.filters[filter]['$or'].push(obj);
        if (filter === 'timestamp') {
            $scope.popupgte.push({'opened': false});
            $scope.popuplte.push({'opened': false});
        }
    };

    //Filter help function: removes filter
    $scope.removeFilter = function (filter, i) {
        $scope.filters[filter]['$or'].splice(i, 1);
        if ($scope.filters[filter]['$or'].length === 0)
            delete $scope.filters[filter];
        if (filter === 'timestamp') {
            $scope.popupgte.splice(i, 1);
            $scope.popuplte.splice(i, 1);
        }
    };

    $scope.toggleAdvancedFilters = function () {
        $scope.advancedFilters = !$scope.advancedFilters;
    };

    //Datepicker help function: Options for datepicker popup
    $scope.dateOptions = {
        formatYear: 'yy',
        startingDay: 1
    };
    //Datepicker help variable: start date and end date popup calendar status gt=greater than, lt= less than
    $scope.popupgte = [];
    $scope.popuplte = [];
    //Datepicker help function: start date and end date popup calendar status change
    $scope.opengte = function (i) {
        $scope.popupgte[i].opened = true;
    };
    $scope.openlte = function (i) {
        $scope.popuplte[i].opened = true;
    };
    //Accordion helper: it blocks opening all the accordion by clicking on only one
    $scope.oneAtATime = true;

    $scope.openStatistics = function () {
        var modalInstance = $uibModal.open({
            templateUrl: 'templates/statsGraphsModal.html',
            controller: 'StatsCtrl',
            resolve: {
                data: function () {
                    return $scope.data;
                }
            },
            size: 'lg'
        });

        modalInstance.result.then(function () {
        }, function () {
        });
    };
}
]);