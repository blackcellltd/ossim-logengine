#!/usr/bin/env python3
import functools
import hashlib

import sqlalchemy
import sshtunnel
import tornado, tornado.ioloop, tornado.web, tornado.process
import tornado.gen
import os
import logging
import sys
import getopt
import configobj
from cryptography.hazmat.primitives.hashes import SHA256
from ossim_logutilities import setup_logger, get_database, get_line_count, convert_mongo_records_to_json, ip_str_to_int, \
    is_valid_ipv6_address, get_ip_str_from_bytes, get_ip_bin_from_str
from ossim_sql_archiver import query_new_records, archive_file
import signal
import time
import multiprocessing
import json
import concurrent
import pymongo
from dateutil import parser
import datetime
import jinja2
import pdfkit
from pprint import pformat

template = jinja2.Template(r"""
<html>
<head>
  <title> Generated report from {{title}}</title>
  <style type="text/css">
    .header-list {
      display: flex;
      flex-flow: row wrap;
      /* justify-content: space-between; */
      align-items: flex-start;
    }
    .header-list-item {
      padding-right: 1em;
      flex-grow: 0;
    }
    .header-list-item code {
      background-color: inherit;
      color: inherit;
    }
    label {
        font-weight: bold;
    }
    pre {
        font-family: Consolas,monospace;
    }
    /* custom bootstrap */
    html{font-family:sans-serif;-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%}body{margin:0}article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,section,summary{display:block}audio,canvas,progress,video{display:inline-block;vertical-align:baseline}audio:not([controls]){display:none;height:0}[hidden],template{display:none}a{background-color:transparent}a:active,a:hover{outline:0}abbr[title]{border-bottom:1px dotted}b,strong{font-weight:bold}dfn{font-style:italic}h1{font-size:2em;margin:0.67em 0}mark{background:#ff0;color:#000}small{font-size:80%}sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}sup{top:-0.5em}sub{bottom:-0.25em}img{border:0}svg:not(:root){overflow:hidden}figure{margin:1em 40px}hr{-webkit-box-sizing:content-box;-moz-box-sizing:content-box;box-sizing:content-box;height:0}pre{overflow:auto}code,kbd,pre,samp{font-family:monospace, monospace;font-size:1em}button,input,optgroup,select,textarea{color:inherit;font:inherit;margin:0}button{overflow:visible}button,select{text-transform:none}button,html input[type="button"],input[type="reset"],input[type="submit"]{-webkit-appearance:button;cursor:pointer}button[disabled],html input[disabled]{cursor:default}button::-moz-focus-inner,input::-moz-focus-inner{border:0;padding:0}input{line-height:normal}input[type="checkbox"],input[type="radio"]{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box;padding:0}input[type="number"]::-webkit-inner-spin-button,input[type="number"]::-webkit-outer-spin-button{height:auto}input[type="search"]{-webkit-appearance:textfield;-webkit-box-sizing:content-box;-moz-box-sizing:content-box;box-sizing:content-box}input[type="search"]::-webkit-search-cancel-button,input[type="search"]::-webkit-search-decoration{-webkit-appearance:none}fieldset{border:1px solid #c0c0c0;margin:0 2px;padding:0.35em 0.625em 0.75em}legend{border:0;padding:0}textarea{overflow:auto}optgroup{font-weight:bold}table{border-collapse:collapse;border-spacing:0}td,th{padding:0}*{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}*:before,*:after{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}html{font-size:10px;-webkit-tap-highlight-color:rgba(0,0,0,0)}body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.42857143;color:#333;background-color:#fff}input,button,select,textarea{font-family:inherit;font-size:inherit;line-height:inherit}a{color:#337ab7;text-decoration:none}a:hover,a:focus{color:#23527c;text-decoration:underline}a:focus{outline:5px auto -webkit-focus-ring-color;outline-offset:-2px}figure{margin:0}img{vertical-align:middle}.img-responsive{display:block;max-width:100%;height:auto}.img-rounded{border-radius:6px}.img-thumbnail{padding:4px;line-height:1.42857143;background-color:#fff;border:1px solid #ddd;border-radius:4px;-webkit-transition:all .2s ease-in-out;-o-transition:all .2s ease-in-out;transition:all .2s ease-in-out;display:inline-block;max-width:100%;height:auto}.img-circle{border-radius:50%}hr{margin-top:20px;margin-bottom:20px;border:0;border-top:1px solid #eee}.sr-only{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0, 0, 0, 0);border:0}.sr-only-focusable:active,.sr-only-focusable:focus{position:static;width:auto;height:auto;margin:0;overflow:visible;clip:auto}[role="button"]{cursor:pointer}h1,h2,h3,h4,h5,h6,.h1,.h2,.h3,.h4,.h5,.h6{font-family:inherit;font-weight:500;line-height:1.1;color:inherit}h1 small,h2 small,h3 small,h4 small,h5 small,h6 small,.h1 small,.h2 small,.h3 small,.h4 small,.h5 small,.h6 small,h1 .small,h2 .small,h3 .small,h4 .small,h5 .small,h6 .small,.h1 .small,.h2 .small,.h3 .small,.h4 .small,.h5 .small,.h6 .small{font-weight:normal;line-height:1;color:#777}h1,.h1,h2,.h2,h3,.h3{margin-top:20px;margin-bottom:10px}h1 small,.h1 small,h2 small,.h2 small,h3 small,.h3 small,h1 .small,.h1 .small,h2 .small,.h2 .small,h3 .small,.h3 .small{font-size:65%}h4,.h4,h5,.h5,h6,.h6{margin-top:10px;margin-bottom:10px}h4 small,.h4 small,h5 small,.h5 small,h6 small,.h6 small,h4 .small,.h4 .small,h5 .small,.h5 .small,h6 .small,.h6 .small{font-size:75%}h1,.h1{font-size:36px}h2,.h2{font-size:30px}h3,.h3{font-size:24px}h4,.h4{font-size:18px}h5,.h5{font-size:14px}h6,.h6{font-size:12px}p{margin:0 0 10px}.lead{margin-bottom:20px;font-size:16px;font-weight:300;line-height:1.4}@media (min-width:768px){.lead{font-size:21px}}small,.small{font-size:85%}mark,.mark{background-color:#fcf8e3;padding:.2em}.text-left{text-align:left}.text-right{text-align:right}.text-center{text-align:center}.text-justify{text-align:justify}.text-nowrap{white-space:nowrap}.text-lowercase{text-transform:lowercase}.text-uppercase{text-transform:uppercase}.text-capitalize{text-transform:capitalize}.text-muted{color:#777}.text-primary{color:#337ab7}a.text-primary:hover,a.text-primary:focus{color:#286090}.text-success{color:#3c763d}a.text-success:hover,a.text-success:focus{color:#2b542c}.text-info{color:#31708f}a.text-info:hover,a.text-info:focus{color:#245269}.text-warning{color:#8a6d3b}a.text-warning:hover,a.text-warning:focus{color:#66512c}.text-danger{color:#a94442}a.text-danger:hover,a.text-danger:focus{color:#843534}.bg-primary{color:#fff;background-color:#337ab7}a.bg-primary:hover,a.bg-primary:focus{background-color:#286090}.bg-success{background-color:#dff0d8}a.bg-success:hover,a.bg-success:focus{background-color:#c1e2b3}.bg-info{background-color:#d9edf7}a.bg-info:hover,a.bg-info:focus{background-color:#afd9ee}.bg-warning{background-color:#fcf8e3}a.bg-warning:hover,a.bg-warning:focus{background-color:#f7ecb5}.bg-danger{background-color:#f2dede}a.bg-danger:hover,a.bg-danger:focus{background-color:#e4b9b9}.page-header{padding-bottom:9px;margin:40px 0 20px;border-bottom:1px solid #eee}ul,ol{margin-top:0;margin-bottom:10px}ul ul,ol ul,ul ol,ol ol{margin-bottom:0}.list-unstyled{padding-left:0;list-style:none}.list-inline{padding-left:0;list-style:none;margin-left:-5px}.list-inline>li{display:inline-block;padding-left:5px;padding-right:5px}dl{margin-top:0;margin-bottom:20px}dt,dd{line-height:1.42857143}dt{font-weight:bold}dd{margin-left:0}@media (min-width:768px){.dl-horizontal dt{float:left;width:160px;clear:left;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.dl-horizontal dd{margin-left:180px}}abbr[title],abbr[data-original-title]{cursor:help;border-bottom:1px dotted #777}.initialism{font-size:90%;text-transform:uppercase}blockquote{padding:10px 20px;margin:0 0 20px;font-size:17.5px;border-left:5px solid #eee}blockquote p:last-child,blockquote ul:last-child,blockquote ol:last-child{margin-bottom:0}blockquote footer,blockquote small,blockquote .small{display:block;font-size:80%;line-height:1.42857143;color:#777}blockquote footer:before,blockquote small:before,blockquote .small:before{content:'\2014 \00A0'}.blockquote-reverse,blockquote.pull-right{padding-right:15px;padding-left:0;border-right:5px solid #eee;border-left:0;text-align:right}.blockquote-reverse footer:before,blockquote.pull-right footer:before,.blockquote-reverse small:before,blockquote.pull-right small:before,.blockquote-reverse .small:before,blockquote.pull-right .small:before{content:''}.blockquote-reverse footer:after,blockquote.pull-right footer:after,.blockquote-reverse small:after,blockquote.pull-right small:after,.blockquote-reverse .small:after,blockquote.pull-right .small:after{content:'\00A0 \2014'}address{margin-bottom:20px;font-style:normal;line-height:1.42857143}code,kbd,pre,samp{font-family:Menlo,Monaco,Consolas,"Courier New",monospace}code{padding:2px 4px;font-size:90%;color:#c7254e;background-color:#f9f2f4;border-radius:4px}kbd{padding:2px 4px;font-size:90%;color:#fff;background-color:#333;border-radius:3px;-webkit-box-shadow:inset 0 -1px 0 rgba(0,0,0,0.25);box-shadow:inset 0 -1px 0 rgba(0,0,0,0.25)}kbd kbd{padding:0;font-size:100%;font-weight:bold;-webkit-box-shadow:none;box-shadow:none}pre{display:block;padding:9.5px;margin:0 0 10px;font-size:13px;line-height:1.42857143;word-break:break-all;word-wrap:break-word;color:#333;background-color:#f5f5f5;border:1px solid #ccc;border-radius:4px}pre code{padding:0;font-size:inherit;color:inherit;white-space:pre-wrap;background-color:transparent;border-radius:0}.pre-scrollable{max-height:340px;overflow-y:scroll}.list-group{margin-bottom:20px;padding-left:0}.list-group-item{position:relative;display:block;padding:10px 15px;margin-bottom:-1px;background-color:#fff;border:1px solid #ddd}.list-group-item:first-child{border-top-right-radius:4px;border-top-left-radius:4px}.list-group-item:last-child{margin-bottom:0;border-bottom-right-radius:4px;border-bottom-left-radius:4px}a.list-group-item,button.list-group-item{color:#555}a.list-group-item .list-group-item-heading,button.list-group-item .list-group-item-heading{color:#333}a.list-group-item:hover,button.list-group-item:hover,a.list-group-item:focus,button.list-group-item:focus{text-decoration:none;color:#555;background-color:#f5f5f5}button.list-group-item{width:100%;text-align:left}.list-group-item.disabled,.list-group-item.disabled:hover,.list-group-item.disabled:focus{background-color:#eee;color:#777;cursor:not-allowed}.list-group-item.disabled .list-group-item-heading,.list-group-item.disabled:hover .list-group-item-heading,.list-group-item.disabled:focus .list-group-item-heading{color:inherit}.list-group-item.disabled .list-group-item-text,.list-group-item.disabled:hover .list-group-item-text,.list-group-item.disabled:focus .list-group-item-text{color:#777}.list-group-item.active,.list-group-item.active:hover,.list-group-item.active:focus{z-index:2;color:#fff;background-color:#337ab7;border-color:#337ab7}.list-group-item.active .list-group-item-heading,.list-group-item.active:hover .list-group-item-heading,.list-group-item.active:focus .list-group-item-heading,.list-group-item.active .list-group-item-heading>small,.list-group-item.active:hover .list-group-item-heading>small,.list-group-item.active:focus .list-group-item-heading>small,.list-group-item.active .list-group-item-heading>.small,.list-group-item.active:hover .list-group-item-heading>.small,.list-group-item.active:focus .list-group-item-heading>.small{color:inherit}.list-group-item.active .list-group-item-text,.list-group-item.active:hover .list-group-item-text,.list-group-item.active:focus .list-group-item-text{color:#c7ddef}.list-group-item-success{color:#3c763d;background-color:#dff0d8}a.list-group-item-success,button.list-group-item-success{color:#3c763d}a.list-group-item-success .list-group-item-heading,button.list-group-item-success .list-group-item-heading{color:inherit}a.list-group-item-success:hover,button.list-group-item-success:hover,a.list-group-item-success:focus,button.list-group-item-success:focus{color:#3c763d;background-color:#d0e9c6}a.list-group-item-success.active,button.list-group-item-success.active,a.list-group-item-success.active:hover,button.list-group-item-success.active:hover,a.list-group-item-success.active:focus,button.list-group-item-success.active:focus{color:#fff;background-color:#3c763d;border-color:#3c763d}.list-group-item-info{color:#31708f;background-color:#d9edf7}a.list-group-item-info,button.list-group-item-info{color:#31708f}a.list-group-item-info .list-group-item-heading,button.list-group-item-info .list-group-item-heading{color:inherit}a.list-group-item-info:hover,button.list-group-item-info:hover,a.list-group-item-info:focus,button.list-group-item-info:focus{color:#31708f;background-color:#c4e3f3}a.list-group-item-info.active,button.list-group-item-info.active,a.list-group-item-info.active:hover,button.list-group-item-info.active:hover,a.list-group-item-info.active:focus,button.list-group-item-info.active:focus{color:#fff;background-color:#31708f;border-color:#31708f}.list-group-item-warning{color:#8a6d3b;background-color:#fcf8e3}a.list-group-item-warning,button.list-group-item-warning{color:#8a6d3b}a.list-group-item-warning .list-group-item-heading,button.list-group-item-warning .list-group-item-heading{color:inherit}a.list-group-item-warning:hover,button.list-group-item-warning:hover,a.list-group-item-warning:focus,button.list-group-item-warning:focus{color:#8a6d3b;background-color:#faf2cc}a.list-group-item-warning.active,button.list-group-item-warning.active,a.list-group-item-warning.active:hover,button.list-group-item-warning.active:hover,a.list-group-item-warning.active:focus,button.list-group-item-warning.active:focus{color:#fff;background-color:#8a6d3b;border-color:#8a6d3b}.list-group-item-danger{color:#a94442;background-color:#f2dede}a.list-group-item-danger,button.list-group-item-danger{color:#a94442}a.list-group-item-danger .list-group-item-heading,button.list-group-item-danger .list-group-item-heading{color:inherit}a.list-group-item-danger:hover,button.list-group-item-danger:hover,a.list-group-item-danger:focus,button.list-group-item-danger:focus{color:#a94442;background-color:#ebcccc}a.list-group-item-danger.active,button.list-group-item-danger.active,a.list-group-item-danger.active:hover,button.list-group-item-danger.active:hover,a.list-group-item-danger.active:focus,button.list-group-item-danger.active:focus{color:#fff;background-color:#a94442;border-color:#a94442}.list-group-item-heading{margin-top:0;margin-bottom:5px}.list-group-item-text{margin-bottom:0;line-height:1.3}.panel{margin-bottom:20px;background-color:#fff;border:1px solid transparent;border-radius:4px;-webkit-box-shadow:0 1px 1px rgba(0,0,0,0.05);box-shadow:0 1px 1px rgba(0,0,0,0.05)}.panel-body{padding:15px}.panel-heading{padding:10px 15px;border-bottom:1px solid transparent;border-top-right-radius:3px;border-top-left-radius:3px}.panel-heading>.dropdown .dropdown-toggle{color:inherit}.panel-title{margin-top:0;margin-bottom:0;font-size:16px;color:inherit}.panel-title>a,.panel-title>small,.panel-title>.small,.panel-title>small>a,.panel-title>.small>a{color:inherit}.panel-footer{padding:10px 15px;background-color:#f5f5f5;border-top:1px solid #ddd;border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel>.list-group,.panel>.panel-collapse>.list-group{margin-bottom:0}.panel>.list-group .list-group-item,.panel>.panel-collapse>.list-group .list-group-item{border-width:1px 0;border-radius:0}.panel>.list-group:first-child .list-group-item:first-child,.panel>.panel-collapse>.list-group:first-child .list-group-item:first-child{border-top:0;border-top-right-radius:3px;border-top-left-radius:3px}.panel>.list-group:last-child .list-group-item:last-child,.panel>.panel-collapse>.list-group:last-child .list-group-item:last-child{border-bottom:0;border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel>.panel-heading+.panel-collapse>.list-group .list-group-item:first-child{border-top-right-radius:0;border-top-left-radius:0}.panel-heading+.list-group .list-group-item:first-child{border-top-width:0}.list-group+.panel-footer{border-top-width:0}.panel>.table,.panel>.table-responsive>.table,.panel>.panel-collapse>.table{margin-bottom:0}.panel>.table caption,.panel>.table-responsive>.table caption,.panel>.panel-collapse>.table caption{padding-left:15px;padding-right:15px}.panel>.table:first-child,.panel>.table-responsive:first-child>.table:first-child{border-top-right-radius:3px;border-top-left-radius:3px}.panel>.table:first-child>thead:first-child>tr:first-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child,.panel>.table:first-child>tbody:first-child>tr:first-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child{border-top-left-radius:3px;border-top-right-radius:3px}.panel>.table:first-child>thead:first-child>tr:first-child td:first-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child td:first-child,.panel>.table:first-child>tbody:first-child>tr:first-child td:first-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child td:first-child,.panel>.table:first-child>thead:first-child>tr:first-child th:first-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child th:first-child,.panel>.table:first-child>tbody:first-child>tr:first-child th:first-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child th:first-child{border-top-left-radius:3px}.panel>.table:first-child>thead:first-child>tr:first-child td:last-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child td:last-child,.panel>.table:first-child>tbody:first-child>tr:first-child td:last-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child td:last-child,.panel>.table:first-child>thead:first-child>tr:first-child th:last-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child th:last-child,.panel>.table:first-child>tbody:first-child>tr:first-child th:last-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child th:last-child{border-top-right-radius:3px}.panel>.table:last-child,.panel>.table-responsive:last-child>.table:last-child{border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel>.table:last-child>tbody:last-child>tr:last-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child,.panel>.table:last-child>tfoot:last-child>tr:last-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child{border-bottom-left-radius:3px;border-bottom-right-radius:3px}.panel>.table:last-child>tbody:last-child>tr:last-child td:first-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child td:first-child,.panel>.table:last-child>tfoot:last-child>tr:last-child td:first-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child td:first-child,.panel>.table:last-child>tbody:last-child>tr:last-child th:first-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child th:first-child,.panel>.table:last-child>tfoot:last-child>tr:last-child th:first-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child th:first-child{border-bottom-left-radius:3px}.panel>.table:last-child>tbody:last-child>tr:last-child td:last-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child td:last-child,.panel>.table:last-child>tfoot:last-child>tr:last-child td:last-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child td:last-child,.panel>.table:last-child>tbody:last-child>tr:last-child th:last-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child th:last-child,.panel>.table:last-child>tfoot:last-child>tr:last-child th:last-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child th:last-child{border-bottom-right-radius:3px}.panel>.panel-body+.table,.panel>.panel-body+.table-responsive,.panel>.table+.panel-body,.panel>.table-responsive+.panel-body{border-top:1px solid #ddd}.panel>.table>tbody:first-child>tr:first-child th,.panel>.table>tbody:first-child>tr:first-child td{border-top:0}.panel>.table-bordered,.panel>.table-responsive>.table-bordered{border:0}.panel>.table-bordered>thead>tr>th:first-child,.panel>.table-responsive>.table-bordered>thead>tr>th:first-child,.panel>.table-bordered>tbody>tr>th:first-child,.panel>.table-responsive>.table-bordered>tbody>tr>th:first-child,.panel>.table-bordered>tfoot>tr>th:first-child,.panel>.table-responsive>.table-bordered>tfoot>tr>th:first-child,.panel>.table-bordered>thead>tr>td:first-child,.panel>.table-responsive>.table-bordered>thead>tr>td:first-child,.panel>.table-bordered>tbody>tr>td:first-child,.panel>.table-responsive>.table-bordered>tbody>tr>td:first-child,.panel>.table-bordered>tfoot>tr>td:first-child,.panel>.table-responsive>.table-bordered>tfoot>tr>td:first-child{border-left:0}.panel>.table-bordered>thead>tr>th:last-child,.panel>.table-responsive>.table-bordered>thead>tr>th:last-child,.panel>.table-bordered>tbody>tr>th:last-child,.panel>.table-responsive>.table-bordered>tbody>tr>th:last-child,.panel>.table-bordered>tfoot>tr>th:last-child,.panel>.table-responsive>.table-bordered>tfoot>tr>th:last-child,.panel>.table-bordered>thead>tr>td:last-child,.panel>.table-responsive>.table-bordered>thead>tr>td:last-child,.panel>.table-bordered>tbody>tr>td:last-child,.panel>.table-responsive>.table-bordered>tbody>tr>td:last-child,.panel>.table-bordered>tfoot>tr>td:last-child,.panel>.table-responsive>.table-bordered>tfoot>tr>td:last-child{border-right:0}.panel>.table-bordered>thead>tr:first-child>td,.panel>.table-responsive>.table-bordered>thead>tr:first-child>td,.panel>.table-bordered>tbody>tr:first-child>td,.panel>.table-responsive>.table-bordered>tbody>tr:first-child>td,.panel>.table-bordered>thead>tr:first-child>th,.panel>.table-responsive>.table-bordered>thead>tr:first-child>th,.panel>.table-bordered>tbody>tr:first-child>th,.panel>.table-responsive>.table-bordered>tbody>tr:first-child>th{border-bottom:0}.panel>.table-bordered>tbody>tr:last-child>td,.panel>.table-responsive>.table-bordered>tbody>tr:last-child>td,.panel>.table-bordered>tfoot>tr:last-child>td,.panel>.table-responsive>.table-bordered>tfoot>tr:last-child>td,.panel>.table-bordered>tbody>tr:last-child>th,.panel>.table-responsive>.table-bordered>tbody>tr:last-child>th,.panel>.table-bordered>tfoot>tr:last-child>th,.panel>.table-responsive>.table-bordered>tfoot>tr:last-child>th{border-bottom:0}.panel>.table-responsive{border:0;margin-bottom:0}.panel-group{margin-bottom:20px}.panel-group .panel{margin-bottom:0;border-radius:4px}.panel-group .panel+.panel{margin-top:5px}.panel-group .panel-heading{border-bottom:0}.panel-group .panel-heading+.panel-collapse>.panel-body,.panel-group .panel-heading+.panel-collapse>.list-group{border-top:1px solid #ddd}.panel-group .panel-footer{border-top:0}.panel-group .panel-footer+.panel-collapse .panel-body{border-bottom:1px solid #ddd}.panel-default{border-color:#ddd}.panel-default>.panel-heading{color:#333;background-color:#f5f5f5;border-color:#ddd}.panel-default>.panel-heading+.panel-collapse>.panel-body{border-top-color:#ddd}.panel-default>.panel-heading .badge{color:#f5f5f5;background-color:#333}.panel-default>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#ddd}.panel-primary{border-color:#337ab7}.panel-primary>.panel-heading{color:#fff;background-color:#337ab7;border-color:#337ab7}.panel-primary>.panel-heading+.panel-collapse>.panel-body{border-top-color:#337ab7}.panel-primary>.panel-heading .badge{color:#337ab7;background-color:#fff}.panel-primary>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#337ab7}.panel-success{border-color:#d6e9c6}.panel-success>.panel-heading{color:#3c763d;background-color:#dff0d8;border-color:#d6e9c6}.panel-success>.panel-heading+.panel-collapse>.panel-body{border-top-color:#d6e9c6}.panel-success>.panel-heading .badge{color:#dff0d8;background-color:#3c763d}.panel-success>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#d6e9c6}.panel-info{border-color:#bce8f1}.panel-info>.panel-heading{color:#31708f;background-color:#d9edf7;border-color:#bce8f1}.panel-info>.panel-heading+.panel-collapse>.panel-body{border-top-color:#bce8f1}.panel-info>.panel-heading .badge{color:#d9edf7;background-color:#31708f}.panel-info>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#bce8f1}.panel-warning{border-color:#faebcc}.panel-warning>.panel-heading{color:#8a6d3b;background-color:#fcf8e3;border-color:#faebcc}.panel-warning>.panel-heading+.panel-collapse>.panel-body{border-top-color:#faebcc}.panel-warning>.panel-heading .badge{color:#fcf8e3;background-color:#8a6d3b}.panel-warning>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#faebcc}.panel-danger{border-color:#ebccd1}.panel-danger>.panel-heading{color:#a94442;background-color:#f2dede;border-color:#ebccd1}.panel-danger>.panel-heading+.panel-collapse>.panel-body{border-top-color:#ebccd1}.panel-danger>.panel-heading .badge{color:#f2dede;background-color:#a94442}.panel-danger>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#ebccd1}.clearfix:before,.clearfix:after,.dl-horizontal dd:before,.dl-horizontal dd:after,.panel-body:before,.panel-body:after{content:" ";display:table}.clearfix:after,.dl-horizontal dd:after,.panel-body:after{clear:both}.center-block{display:block;margin-left:auto;margin-right:auto}.pull-right{float:right !important}.pull-left{float:left !important}.hide{display:none !important}.show{display:block !important}.invisible{visibility:hidden}.text-hide{font:0/0 a;color:transparent;text-shadow:none;background-color:transparent;border:0}.hidden{display:none !important}.affix{position:fixed}
  </style>
</head>
<body>
  <h1>{{title}} </h1>
<pre><code>{{filter -}}
</code></pre>
  <div class="panel-group">
    {% for record in records %}
      <div class="panel panel-default">
        <div class="panel-heading header-list">
          {% for field in header_fields %}
            <div class="header-list-item">
              <label>{{ field.name }}:</label>
              {% if loop.last %}
                <code>{{ record[field.key] }}</code>
              {% else %}
                {{ record[field.key] }}
              {% endif %}
            </div>
          {% endfor %}
        </div>
        <div class="panel-body">
          {% for field in footer_fields if record[field.key] %}
            {% set val = record[field.key] %}
            <div>
              <label>{{field.name}}:</label>
              <code>
                {% if val is string and "\n" in val %}
                  {% for line in val.splitlines() %}
                    {{ line }} {% if loop.last %} <br> {% endif %}
                  {% endfor %}
                {% else %}
                    {{ val }}
                {% endif %}
              </code>
            </div>
          {% endfor %}
        </div>
      </div>
    {% endfor %}
  </div>
</body>
</html>
""")

header_fields = [
    {"name": "Timestamp",        "key": "timestamp"},
    {"name": "Source IP",        "key": "ip_src"},
    {"name": "Destination IP",   "key": "ip_dst"},
    {"name": "Source Hostname",  "key": "src_hostname"},
    {"name": "Plugin_ID",        "key": "plugin_id"},
    {"name": "Data payload",     "key": "data_payload"},
]

footer_fields = [
    {"name": "Layer4 source port",       "key": "layer4_sport"},
    {"name": "Layer4 destination port",  "key": "layer4_dport"},
    {"name": "Username",                 "key": "username"},
    {"name": "Password",                 "key": "password"},
    {"name": "Source Host",              "key": "src_host"},
    {"name": "Source Net",               "key": "src_net"},
    {"name": "Source MAC",               "key": "src_mac"},
    {"name": "Destination Host",         "key": "dst_host"},
    {"name": "Destination Hostname",     "key": "dst_hostname"},
    {"name": "Destination Net",          "key": "dst_net"},
    {"name": "Destination MAC",          "key": "dst_mac"},
    {"name": "Filename",                 "key": "filename"},
    {"name": "Binary data",              "key": "binary_data"},
    {"name": "Userdata 1",               "key": "userdata1"},
    {"name": "Userdata 2",               "key": "userdata2"},
    {"name": "Userdata 3",               "key": "userdata3"},
    {"name": "Userdata 4",               "key": "userdata4"},
    {"name": "Userdata 5",               "key": "userdata5"},
    {"name": "Userdata 6",               "key": "userdata6"},
    {"name": "Userdata 7",               "key": "userdata7"},
    {"name": "Userdata 8",               "key": "userdata8"},
    {"name": "Userdata 9",               "key": "userdata9"},
]

server_logger = logging.getLogger("ossim_logger.server")


def read_config(config_file, logger):
    """
    Read config file given in config_file argument, parse its body.

    In order for this script to work, the config file must contain at least:
    - The keyword archive_directory: Path to the folder, where the archived files will be stored.
    - Sections called mongo, server, mysql.
    - In the mongo section, the following keywords:
        - database: Name of the database which will be used for mysql archiving.
        - hostname: Hostname where the MongoDB is accessible.
        - port: Port where the MongoDB is accessible.
        - collection: Name of the collection where the log records will be stored.
        - justinsert: The password for the justinsert user for the MongoDB. Generated by mongodb_setup.py.
        - justread: The password for the justread user for the MongoDB. Generated by mongodb_setup.py.

    - In the MySQL section:
        - hostname: Hostname where the MySQL is accessible. If a tunnel_pwd is given, the script will try to use an ssh
tunnel to this hostname.
        - port: Port where the MySQL  is accessible. Same, if a tunnel_pwd is given, the script will try to tunnel to
this portself.
        - username: Username for the MySQL server, which enables access for the server to interact with it.
        - password: Password for the username. Generated by ossim_mysql_setup.py.
    - In the server section:
        - key: Preshared key, for authenticating clients.

    - Optional keywords include:
        - logfile: Name and path of the logfile used.
        - loglevel: Level of logging to be used.
    - Optional keywords in the server section:
        - port: Port where the server will listen.
        - mysql_callback_time: Time interval between calling the MySQL archiving, given in seconds.
        - archive_callback_time: Time interval between calling the file archiving, given in seconds.
    - Optional keywords in the mysql section:
        - database: Default database to connect to.
        - tunnel_pwd: Password for the user called tunnel, on the same computer as the MySQL server. If a password is
        given here, the hostname and port in the mysql section is interpreted as hostname and port for an ssh tunnel.



    :param logger: logger to use
    :param config_file: path to the config file
    """
    try:

        optional = {"logfile": "ossim_logserver.log",
                    "loglevel": "DEBUG",
                    "server": {
                        "port": 8888,

                    },
                    "mongo": {

                    },
                    "ossim": {
                        "database": "alienvault_siem",
                        "tunnel_pwd": "",
                        "mysql_callback_time": 3600,
                        "archive_callback_time": 10800
                    }}

        required = {"archive_directory": None,
                    "server": [],
                    "mongo": ["database", "hostname", "port", "collection", "justinsert", "justread"],
                    "ossim": ["hostname", "port", "username", "password"]}

        parser = configobj.ConfigObj(config_file)

        for key in filter(lambda x: not x == "ossim", required):
            if parser.get(key, None) is None:
                key_type = "Section" if isinstance(required.get(key), dict) else "Keyword"
                logger.error("{} {} not found!".format(key_type, key))
                sys.exit(2)
            elif isinstance(required.get(key), list):
                for subkey in required[key]:
                    if parser[key].get(subkey, None) is None:
                        logger.error("{} not found in section {}!".format(subkey, key))
                        sys.exit(2)

        for key in filter(lambda x: not x == "ossim", required):
            if parser.get(key, None) is None:
                parser[key] = optional[key]
                logger.warning(
                    "The keyword {} was not found, defaulting to default value: {}".format(key, optional[key]))
            elif isinstance(optional.get(key), dict):
                for subkey in optional[key]:
                    if parser[key].get(subkey, None) is None:
                        parser[key][subkey] = optional[key][subkey]
                        logger.warning(
                            "The keyword {} was not found in section {}, defaulting to default value: {}".format(subkey,
                                                                                                                 key,
                                                                                                                 optional[
                                                                                                                     key][
                                                                                                                     subkey]))

        all_predef_key = set(
            list(filter(lambda x: not x == "ossim", required)) + list(filter(lambda x: not x == "ossim", optional)))
        # For every section, that has not been checked (so any section describing an ossim setup)
        for key in filter(lambda x: x not in all_predef_key, parser.keys()):
            # If the custom key is not a section, error and exit
            if not isinstance(parser.get(key), dict):
                logger.error("An Ossim config must be a section, {} is not a section!".format(key))
                sys.exit(2)
            # For each required key, check for presence.
            for subkey in required.get("ossim"):
                if subkey not in parser.get(key).keys():
                    logger.error("{} not found in custom section {}!".format(subkey, key))
                    sys.exit(2)
            # For each optional key not present, use default value
            for subkey in optional.get("ossim"):
                if subkey not in parser.get(key).keys():
                    parser[key][subkey] = optional["ossim"][subkey]
                    logger.warning(
                        "The keyword {} was not found in custom section {}, defaulting to default value: {}".format(
                            subkey, key, optional["ossim"][subkey]))

        setup_logger(parser, logger)

        return parser, set(filter(lambda x: x not in all_predef_key, parser.keys()))

    except IOError:
        logger.error("Unable to read config file {configfile}!", configfile=parser.filename)
        sys.exit(2)
    except configobj.ParseError:
        logger.error("Error in config file {configfile} format!", configfile=parser.filename)


is_closing = False
client = None
db = None


def signal_handler(signum, frame):
    """
    Handle SIGINT signals, set 'is_closing' for the callback.

    :param signum:
    :param frame:
    """
    global is_closing
    server_logger.info('Got SIGINT, exiting server...')
    is_closing = True


def try_exit():
    """
    Callback function, close the server if 'is_closing' is True.
    """
    global is_closing
    if is_closing:
        # clean up here
        tornado.ioloop.IOLoop.instance().stop()
        server_logger.info('Exit successful')


class JSON(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

    @tornado.gen.coroutine
    def post(self):
        global cli, db
        names = {"ip_proto": "Ip proto",
                 "tzone": "Timezone",
                 "_id": "_ID",
                 "ctx": "CTX:",
                 "id": "ID",
                 "ossim_asset_src": "Ossim asset source",
                 "ossim_asset_dst": "Ossim asset destination",
                 "ossim_correlation": "Ossim correlation",
                 "ossim_priority": "Ossim priority",
                 "ossim_reliability": "Ossim reliability",
                 "ossim_risk_a": "Ossim risk a",
                 "ossim_risk_c": "Ossim risk c",
                 "device_i": "Device ID",
                 "layer4_sport": "Layer4 source port",
                 "username": "Username",
                 "password": "Password",
                 "src_hostname": "Source Hostname",
                 "src_net": "Source Net",
                 "src_mac": "Source MAC",
                 "dst_host": "Destination Host",
                 "dst_hostname": "Destination Hostname",
                 "dst_net": "Destination Net",
                 "dst_mac": "Destination MAC",
                 "filename": "Filename",
                 "binary_data": "Binary data",
                 "ip_src": "Source IP",
                 "ip_dst": "Destination IP",
                 "timestamp": "Timestamp",
                 "plugin_id": "Plugin ID",
                 "plugin_sid": "Plugin SID",
                 "ossim_id": "Ossim ID"
                 }
        payload = json.loads(self.request.body.decode("utf8"))
        report = payload.get("report", None)
        pageSize = payload["pageSize"]
        currentPage = payload["currentPage"]
        query = ""
        filter = payload["filter"]
        if len(filter) == 0:
            filter = {}

        store_in_binary = ["src_host", "dst_host", "dst_net", "src_net", "ip_src", "ip_dst"]
        if "$and" in filter:
            for ors in filter["$and"]:
                for filt in ors["$or"]:
                    for key, value in filt.items():
                        if key != 'timestamp':
                            query += str(names[key]) + " is " + str(value) + "<p>"

                    if "timestamp" in filt:
                        if "$gte" in filt["timestamp"]:
                            filt["timestamp"]["$gte"] = parser.parse(filt["timestamp"]["$gte"])
                            query += str(names["timestamp"]) + " greater than " + filt["timestamp"]["$gte"].isoformat() + "<p>"
                        if "$lte" in filt["timestamp"]:
                            filt["timestamp"]["$lte"] = parser.parse(filt["timestamp"]["$lte"])
                            query += str(names["timestamp"]) + " less than " + filt["timestamp"]["$lte"].isoformat() + "<p>"

                    for key in [k for k in store_in_binary if k in filt]:
                        filt[key] = get_ip_bin_from_str(filt[key])

        def cb():
            cursor = db.log.find(filter)
            records = list(cursor.skip(((currentPage - 1) * pageSize) if currentPage > 1 else 0).limit(pageSize))
            for rec in records:
                if len(list(db.archived.find({"batch_name":rec["batch_name"]}))) > 0:
                    rec["isarchived"] = True
                else:
                    rec["isarchived"] = False

            return cursor.count(), records

        if report:
            yield from self.generate_report(query, report, filter)
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            total_count, records = yield executor.submit(cb)

        json_mongo_records = convert_mongo_records_to_json(records, server_logger)
        json_mongo_records.insert(0, total_count)

        self.finish(json.dumps(json_mongo_records))

    def html_report(self, title, filter, records):
        html = template.render(
            title=title,
            filter=pformat(filter),
            header_fields=header_fields,
            footer_fields=footer_fields,
            records=records
        )
        return html

    def pdf_report(self, title, filter, records):
        html = self.html_report(title, filter, records)
        pdf  = pdfkit.from_string(html, False)
        return pdf

    def generate_report(self, query, report, filter):
        title = datetime.datetime.now().isoformat()
        recordss = []
        if report == "html" or report == "pdf":

            count = db.log.find(filter).count()
            itersize = 2000
            for i in range(0, count, itersize):
                def step():
                    cursor = db.log.find(filter)
                    return cursor.count(), list(cursor.skip(i).limit(itersize).batch_size(itersize))

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    total_count, records = yield executor.submit(step)

                recordss = recordss + convert_mongo_records_to_json(records, server_logger)
        if report == "pdf":
            self.set_header('Content-Type', 'application/pdf; charset="utf-8"')
            self.set_header('Content-Disposition', 'attachment; filename="test.pdf"')
            try:
                gencontent = self.pdf_report(title, query, recordss)
            except Exception as e:
                server_logger.error(e)
        else:
            gencontent = self.html_report(title, query, recordss)
        self.write(gencontent)
        self.finish()


class Status(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

    @tornado.gen.coroutine
    def get(self):
        self.finish("Up at: " + time.strftime("%Y %m %d %H:%M:%S", time.localtime()))


class ActivePlugins(tornado.web.RequestHandler):
    def initialize(self, config, ossim_keys):
        self.config = config
        self.ossim_keys = ossim_keys

    @tornado.gen.coroutine
    def post(self):
        global db, cli
        plugins = []
        sids = []

        for key in self.ossim_keys:
            activePlugins = []
            for p in db.log.aggregate([{'$match':{'ossim_id': self.config[key]['id']}},{"$group": {"_id": {"plugin_id": "$plugin_id"}}}]):
                try:
                    activePlugins.append(int(p['_id']['plugin_id']))
                except TypeError:  # if plugin_id is None, thats baaad.
                    server_logger.debug(repr(p))
    
            activePairs = []
            for p in db.log.aggregate([{'$match':{'ossim_id':self.config[key]['id']}},{"$group": {"_id": {"plugin_id": "$plugin_id", "plugin_sid": "$plugin_sid"}}}]):
                try:
                    activePairs.append({int(p['_id']['plugin_id']), int(p['_id']['plugin_sid'])})
                except KeyError or TypeError:  # if plugin_id or plugin_sid is None, thats baaad.
                    server_logger.debug(repr(p))

            self._gather_plugin_names(plugins, sids, key, activePlugins, activePairs)
        self.finish(json.dumps({"plugins": plugins, "sids": sids}))

    def _gather_plugin_names(self, plugins, sids, key, activePlugins, activePairs):
        using_tunnel = False if self.config[key]["tunnel_pwd"] == "" else True
        try:
            if using_tunnel:
                login_data = {
                    "user": self.config[key]["username"],
                    "pw": self.config[key]["password"],
                    "port": "8081",
                    "hostname": "127.0.0.1",
                    "db": "alienvault_siem"

                }
                tunnel = sshtunnel.SSHTunnelForwarder(
                    (self.config[key]["hostname"], int(self.config[key]["port"])),
                    ssh_username="tunnel",
                    ssh_password=self.config[key]["tunnel_pwd"],
                    remote_bind_address=('127.0.0.1', 3306)
                )
                tunnel.start()
                login_data["port"] = tunnel.local_bind_port
            else:
                login_data = {
                    "user": self.config[key]["username"],
                    "pw": self.config[key]["password"],
                    "port": self.config[key]["port"],
                    "hostname": self.config[key]["hostname"],
                    "db": "alienvault_siem"
                }
            engine = sqlalchemy.create_engine('mysql+pymysql://{user}:{pw}@{hostname}:{port}/{db}'.format(**login_data))
            with engine.connect() as con:
                rs = con.execute(
                    "SELECT alienvault.plugin.id, alienvault.plugin.name FROM alienvault.plugin WHERE alienvault.plugin.id IN %s;",
                    [(activePlugins,)])
                for row in rs:
                    plugins.append({'id': row.id, 'name': row.name, 'ossim_id': self.config[key]['id'], 'ossim_name': self.config[key]['name']})
                rs = con.execute(
                    "SELECT alienvault.plugin_sid.plugin_id, alienvault.plugin_sid.sid, alienvault.plugin_sid.name FROM alienvault.plugin_sid WHERE (alienvault.plugin_sid.plugin_id, alienvault.plugin_sid.sid) IN %s;",
                    [(activePairs,)])
                for row in rs:
                    sids.append({'id': row.plugin_id, 'sid': row.sid, 'name': row.name, 'ossim_id': self.config[key]['id'], 'ossim_name': self.config[key]['name']})
        finally:
            if using_tunnel:
                tunnel.stop()


class StatsBarGraph(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

    @tornado.gen.coroutine
    def post(self):
        global cli, db
        payload = json.loads(self.request.body.decode("utf8"))
        server_logger.info(str(repr(payload)))
        count = payload.get("count", 10)
        resolution = payload.get("resolution", "hours")
        if resolution not in ["months", "weeks", "days", "hours"]:
            resolution = "hours"
        offset = payload.get("offset", 0)

        # ugly hack to overcome that months are unfortunately not supported by timedelta
        # feel free to fix
        # and sorry for this mess
        months = 1
        if resolution == "months":
            resolution = "weeks"
            months = 4

        now = datetime.datetime.now()
        data = []
        labels = []
        for i in range(count):
            # instiate with the 'value of resolution' as a parameter so if res. is days then days=..., if months then months=... in parameters
            """
            >>> res = "hours"
            >>> str(repr(datetime.timedelta(**{res:1})))
            'datetime.timedelta(0, 3600)'
            >>> res = "weeks"
            >>> str(repr(datetime.timedelta(**{res:1})))
            'datetime.timedelta(7)'
            """
            gte = now - datetime.timedelta(**{resolution: (offset + i + 1) * months})
            lte = now - datetime.timedelta(**{resolution: (offset + i) * months})
            filt = {'timestamp': {'$gte': gte, '$lte': lte}}
            res = db.log.find(filt).count()
            data = [res] + data
            labels = [gte.isoformat(), lte.isoformat()] + labels

        stats = {"requested": data, "labels": labels}
        self.finish(json.dumps(stats))


class PluginsPieChart(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

    @tornado.gen.coroutine
    def post(self):
        global cli, db
        log_count = db.log.count()
        pwp = []
        for c in db.log.aggregate([{'$group': {'_id': '$plugin_id', 'count': {'$sum': 1}}}]):
            c['count'] = float("{0:.2f}".format((c['count'] / log_count * 100)))
            pwp.append(c)

        stats = {"plugins_with_percentage": pwp}
        self.finish(json.dumps(stats))


class Count(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

    @tornado.gen.coroutine
    def post(self):
        global cli, db
        log_count = db.log.count()
        stats = {"count": log_count}
        self.finish(json.dumps(stats))


web_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")


def start_mysql_archiving(config, key, sql_lock):
    """ Start a new process, which archives the MySQL records into the MongoDB."""
    multiprocessing.Process(target=query_new_records, args=(config, key, sql_lock)).start()


def start_archiving(config, key, sql_lock):
    """ Start a new process, which archives the recently copied MySQL records into files, and timestamps them."""
    multiprocessing.Process(target=archive_file, args=(config, key, sql_lock)).start()


def usage():
    """
    Prints the usage of the program.
    """
    print("usage: ossim_logserver.py [-c/--config configfile] [-nc/--no-callback]")


def main(argv):
    """
    Entry point of the file. Parses the command line for options, and starts the Tornado webserver.
    """
    config_file = '/etc/ossim/logserver.conf'
    global client, db, server_logger

    try:
        # Get config file arg (if exists)
        opts, args = getopt.getopt(argv, 'c:nc', ['config=', 'no-callback'])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    use_callbacks = True
    for opt, arg in opts:
        if opt in ("-c", "--config"):
            config_file = arg
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        if opt in ("-nc", "--no-callback"):
            use_callbacks = False

    config, ossim_keys = read_config(config_file, server_logger)
    if not os.path.isdir(config['archive_directory']):
        os.mkdir(config['archive_directory'])

    client = pymongo.MongoClient(
        "{hostname}:{port}".format(hostname=config["mongo"]["hostname"], port=config["mongo"]["port"]))
    db = client.get_database(config["mongo"]["database"])
    db.authenticate("justread", config["mongo"]["justread"])

    staticpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'web')
    app = tornado.web.Application(
        [
            # (r"/reprocess", Reprocess, dict(config=config)),
            (r"/status", Status, dict(config=config)),
            (r"/statsBarGraph", StatsBarGraph, dict(config=config)),
            (r"/count", Count, dict(config=config)),
            (r"/pluginsPieChart", PluginsPieChart, dict(config=config)),
            (r"/json", JSON, dict(config=config)),
            (r"/activePlugins", ActivePlugins, dict(config=config, ossim_keys=ossim_keys)),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': staticpath})
        ]
    )

    signal.signal(signal.SIGINT, signal_handler)
    app.listen(config["server"]["port"])

    tornado.ioloop.PeriodicCallback(try_exit, 300).start()

    if use_callbacks:
        for key in ossim_keys:
            sql_lock = multiprocessing.RLock()
            sql_callback = functools.partial(start_mysql_archiving, config, key, sql_lock)
            tornado.ioloop.PeriodicCallback(sql_callback, float(config[key]["mysql_callback_time"]) * 1000).start()

            archiver_callback = functools.partial(start_archiving, config, key, sql_lock)
            tornado.ioloop.PeriodicCallback(archiver_callback,
                                            float(config[key]["archive_callback_time"]) * 1000).start()

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    # Call main with the command-line argument (if exists)
    main(sys.argv[1:])
