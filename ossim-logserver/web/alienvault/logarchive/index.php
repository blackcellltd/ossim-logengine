<?php
/** Routing for the ajax proxy */
$PROX_PREFIX = 'logarchive/';
$SERVER_IP = '!SERVER!';
$SERVER_PORT = '!PORT!';

$isJSON = strpos($_SERVER["CONTENT_TYPE"], "json") > 0;
$data = json_decode($HTTP_RAW_POST_DATA, true);

if ($isJSON && $data['path']) {
    $path = $data['path'];
    if (strpos($path, $PROX_PREFIX) != 0) {
        die(500);
    }
    $path = substr($path, strlen($PROX_PREFIX));

    $ch = curl_init("https://$SERVER_IP:$SERVER_PORT/$path");
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data, true));
    curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type:application/json'));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $content = curl_exec($ch);

    $myfile = fopen("/tmp/REP.pdf", "w") or die("Unable to open file!");
    fwrite($myfile, $content);
    fclose($myfile);

    curl_close($ch);

    if ($data['report'] == "pdf") {
        header('Content-Type: application/pdf; charset="utf-8"');
        header('Content-Disposition: attachment; filename="report.pdf"');
        header('Content-Length: '.strlen($content));
        readfile("/tmp/REP.pdf");
        die();
    }
    echo $content;
    die();
}
?>


<?php
require_once 'av_init.php';
?>

<!DOCTYPE html>
<html id=ngApp ng-app="bcloggerApp">

<head lang="en">
    <meta http-equiv="Pragma" content="no-cache"/>
    <?php

    //CSS Files
    $_files = array(
        array('src' => '/logarchive/allLogarchive.css', 'def_path' => FALSE),
    );

    Util::print_include_files($_files, 'css');

    //JS Files
    $_files = array(
        array('src' => 'jquery.min.js', 'def_path' => TRUE),
        array('src' => 'jquery-ui.min.js', 'def_path' => TRUE),
        array('src' => 'utils.js', 'def_path' => TRUE),
        array('src' => 'token.js', 'def_path' => TRUE),
        array('src' => 'jquery.tipTip.js', 'def_path' => TRUE),
        array('src' => 'greybox.js', 'def_path' => TRUE),
        array('src' => 'coolbox.js', 'def_path' => TRUE),
        array('src' => 'notification.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/jquery/dist/jquery.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/bootstrap/dist/js/bootstrap.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/charts/Chart.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/angular/angular.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/charts/angular-chart.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/angular-route/angular-route.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/angular-bootstrap/ui-bootstrap.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/components/angular-bootstrap/ui-bootstrap-tpls.min.js', 'def_path' => FALSE),
        array('src' => '/logarchive/js/controllers/app.js', 'def_path' => FALSE),
    );
    Util::print_include_files($_files, 'js');

    ?>
    <title>Log archive</title>
</head>
<body ng-controller="resultsController">
<button class="btn" ng-click="openStatistics()">Statistics</button>
<button class="btn {{ originalResultLength > 5000 ? 'disabled' : '' }}" ng-click="generateReport('pdf')">Generate report (PDF)</button>
<button class="btn {{ originalResultLength > 5000 ? 'disabled' : '' }}" ng-click="generateReport('html')">Generate report (HTML)</button>
<div>
    <h3>Choose filters - <b>{{originalResultLength | number}}</b> / {{numberofLogs | number}} logs selected</h3>
    <div class="input-group">
        <select ng-model="currentFilter" class="form-control" ng-init="currentFilter = 'username'">
            <option ng-repeat="filtertype in filtertypes" value="{{filtertype.name}}">{{filtertype.hrName}}</option>
            <!--timestamp needs special care and love with its fancy date chooser-->
            <option value="timestamp">Timestamp</option>
            <option value="plugin_id">Plugins</option>
            <option ng-if="advancedFilters" ng-repeat="filtertype in advancedFiltertypes" value="{{filtertype.name}}">
                {{filtertype.hrName}}
            </option>
        </select>
        <span class="input-group-btn">
          <button type="button" title="Add filter" ng-click="addFilter(currentFilter)" class="btn btn-default">Add a filter</button>
          <button type="button" title="Advanced filters" ng-click="toggleAdvancedFilters()"
                  class="btn btn-default {{advancedFilters ?'btn-danger':''}}">Advanced filters</button>
          <button type="button" ng-click="pageChangedOrSearch(true)" class="btn btn-primary">Search</button>
        </span>
    </div><!-- input-group-->
    <!--Showing added filters -->
    <hr/>
    <div ng-repeat="filtertype in filtertypes">
        <div ng-repeat="filter in filters[filtertype.name]['$or']">
            {{filtertype.hrName}}: <br/>
            <div class="input-group">
                <form ng-submit="pageChangedOrSearch(true)">
                    <input type="text" ng-model="filters[filtertype.name]['$or'][$index][filtertype.name]"
                           class="form-control input-sm" placeholder="{{filtertype.placeholder}}"/>
                </form>
                <span class="input-group-btn">
              <button class="btn btn-default btn-sm" type="button" ng-click="removeFilter(filtertype.name, $index)">
                <span class="glyphicon glyphicon-minus"></span>
              </button>
            </span>
            </div>
        </div>
    </div>

    <div ng-repeat="filter in filters['plugin_id']['$or']">
        Plugin: <br/>
        <div class="input-group">
            <form ng-submit="pageChangedOrSearch(true)">
                <select ng-model="filters['plugin_id']['$or'][$index]['plugin_id']" class="form-control">
                    <option ng-repeat="plugin in activePlugins" value="{{ Plugin(plugin.id,plugin.ossim_id) }}">{{plugin.name + " on " + plugin.ossim_name + "(" + plugin.ossim_id + ")"}}</option>
                </select>
                With SID:<input type="checkbox" ng-model="withSid[$index]" ng-change="sidToggleChanged($index, withSid[$index])">
                <select ng-if="withSid[$index]" ng-model="filters['plugin_id']['$or'][$index]['plugin_sid']" class="form-control" convert-to-number>
                    <option ng-repeat="sid in sids | filter:filterSid(filters['plugin_id']['$or'][$index]['plugin_id'])" value="{{sid.sid}}">
                        {{sid.name}}
                    </option>
                </select>
            </form>
            <span class="input-group-btn">
              <button class="btn btn-default btn-sm" type="button" ng-click="removeFilter('plugin_id', $index)">
                <span class="glyphicon glyphicon-minus"></span>
              </button>
            </span>
        </div>
    </div>

    <div ng-repeat="filter in filters['timestamp']['$or']">
        Timestamp:
        <div class="input-group">
            <div>
                Start date:
                <p class="input-group">
                    <input type="datetime-local" class="form-control" uib-datepicker-popup
                           ng-model-options="{timezone: 'UTC'}"
                           ng-model="filters['timestamp']['$or'][$index]['timestamp']['$gte']"
                           is-open="popupgte[$index].opened" datepicker-popup="dateOptions"
                           datepicker-options="dateOptions"
                           ng-required="true" close-text="Close"/>
                    <span class="input-group-btn">
                 <button type="button" class="btn btn-default" ng-click="opengte($index)"><i
                         class="glyphicon glyphicon-calendar"></i></button>
                </span>
                </p>
            </div>
            <div>
                End date:
                <p class="input-group">
                    <input type="datetime-local" class="form-control" uib-datepicker-popup
                           ng-model-options="{timezone: 'UTC'}"
                           ng-model="filters['timestamp']['$or'][$index]['timestamp']['$lte']"
                           is-open="popuplte[$index].opened" datepicker-options="dateOptions" ng-required="true"
                           close-text="Close"/>
                    <span class="input-group-btn">
                  <button type="button" class="btn btn-default" ng-click="openlte($index)"><i
                          class="glyphicon glyphicon-calendar"></i></button>
                </span>
                </p>
            </div>
            <span class="input-group-btn">
              <button class="btn btn-default btn-sm" type="button" ng-click="removeFilter('timestamp', $index)">
                <span class="glyphicon glyphicon-minus"></span>
              </button>
            </span>

        </div>
    </div>
    <div ng-if="advancedFilters">
        <div ng-repeat="filtertype in advancedFiltertypes">
            <div ng-repeat="filter in filters[filtertype.name]['$or']">
                {{filtertype.hrName}}: <br/>
                <div class="input-group">
                    <form ng-submit="pageChangedOrSearch(true)">
                        <input type="text" ng-model="filters[filtertype.name]['$or'][$index][filtertype.name]"
                               class="form-control input-sm" placeholder="{{filtertype.placeholder}}"/>
                    </form>
                    <span class="input-group-btn">
              <button class="btn btn-default btn-sm" type="button" ng-click="removeFilter(filtertype.name, $index)">
                <span class="glyphicon glyphicon-minus"></span>
              </button>
            </span>
                </div>
            </div>
        </div>
    </div>

    <hr/>
</div> <!--colleft -->
<!-- END OF FILTERS -->

<div ng-show="results">

    <!-- pagination buttons -->
    <div class="row">
        <div class="col-xs-3 col-sm-3">
            <div class="input-group input-group-btn">
                <button type="button" ng-repeat="size in numPerPages" class="btn {{size === numPerPage ? 'btn-primary' : 'btn-default'}}" ng-click="setNumPerPage(size)">
                    {{size}}
                </button>
            </div>
        </div>
        <div class="col-xs-9 col-sm-9">
            <ul uib-pagination total-items="originalResultLength" ng-model="currentPage" force-ellipses="true" max-size="maxPageSize" class="pagination-sm" boundary-link-numbers="false" ng-change="pageChangedOrSearch(false)"></ul>
        </div>
    </div>


    <!-- Custom accordion template, so that angular-bootstrap does not mess up my accordion headers -->
    <script type="text/ng-template" id="group-template.html">
        <div class="panel panel-default">
            <div class="panel-heading">
                <div href tabindex="0" class="accordion-toggle" ng-click="toggleOpen()" uib-accordion-transclude="heading">
                    <div uib-accordion-header ng-class="{'text-muted': isDisabled}">
                        {{heading}}
                    </div>
                </div>
            </div>
            <div class="panel-collapse collapse" uib-collapse="!isOpen">
                <div class="panel-body" ng-transclude>            
                </div>
            </div>
        </div>
    </script>


    <!-- records (with accordion) -->
    <uib-accordion close-others="oneAtATime">
        <div uib-accordion-group ng-repeat="result in results" class="panel panel-default" template-url="group-template.html">
            
            <uib-accordion-heading>
                <div class="result-record-container">
                    <img ng-if="result.isarchived" src="components/checkmark.png" alt="Archived">
                    <div ng-repeat="field in defaultFields" ng-if="field.fieldName != 'data_payload'" class="result-record-item">
                        <label> {{ field.name }}: </label>
                        {{ field.formatter(result[field.fieldName]) }}
                    </div>
                    <div class="result-record-item">
                        <label> Plugin </label>
                        {{ getPluginName(result.plugin_id, result.ossim_id) }}
                    </div>
                    <div class="result-record-item">
                        <code>{{ result['data_payload'] }}</code>
                    </div>
                </div>
            </uib-accordion-heading>

        
            <div ng-repeat="field in getAccordionFields()" ng-if="!!result[field.fieldName]">
                <label>{{ field.name }}:</label>
                <code>{{ result[field.fieldName] }}</code>
            </div>
        
        </div>
    </uib-accordion>

    <!-- pagination buttons -->
    <div class="row">
        <ul uib-pagination total-items="originalResultLength" ng-model="currentPage" force-ellipses="true" max-size="maxPageSize" class="pagination-sm" boundary-link-numbers="false" ng-change="pageChangedOrSearch(false)">
        </ul>
    </div>

</div>

    
</body>