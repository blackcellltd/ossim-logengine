import jinja2
import pdfkit

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
    /* custom bootstrap */
    html{font-family:sans-serif;-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%}body{margin:0}article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,section,summary{display:block}audio,canvas,progress,video{display:inline-block;vertical-align:baseline}audio:not([controls]){display:none;height:0}[hidden],template{display:none}a{background-color:transparent}a:active,a:hover{outline:0}abbr[title]{border-bottom:1px dotted}b,strong{font-weight:bold}dfn{font-style:italic}h1{font-size:2em;margin:0.67em 0}mark{background:#ff0;color:#000}small{font-size:80%}sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}sup{top:-0.5em}sub{bottom:-0.25em}img{border:0}svg:not(:root){overflow:hidden}figure{margin:1em 40px}hr{-webkit-box-sizing:content-box;-moz-box-sizing:content-box;box-sizing:content-box;height:0}pre{overflow:auto}code,kbd,pre,samp{font-family:monospace, monospace;font-size:1em}button,input,optgroup,select,textarea{color:inherit;font:inherit;margin:0}button{overflow:visible}button,select{text-transform:none}button,html input[type="button"],input[type="reset"],input[type="submit"]{-webkit-appearance:button;cursor:pointer}button[disabled],html input[disabled]{cursor:default}button::-moz-focus-inner,input::-moz-focus-inner{border:0;padding:0}input{line-height:normal}input[type="checkbox"],input[type="radio"]{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box;padding:0}input[type="number"]::-webkit-inner-spin-button,input[type="number"]::-webkit-outer-spin-button{height:auto}input[type="search"]{-webkit-appearance:textfield;-webkit-box-sizing:content-box;-moz-box-sizing:content-box;box-sizing:content-box}input[type="search"]::-webkit-search-cancel-button,input[type="search"]::-webkit-search-decoration{-webkit-appearance:none}fieldset{border:1px solid #c0c0c0;margin:0 2px;padding:0.35em 0.625em 0.75em}legend{border:0;padding:0}textarea{overflow:auto}optgroup{font-weight:bold}table{border-collapse:collapse;border-spacing:0}td,th{padding:0}*{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}*:before,*:after{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}html{font-size:10px;-webkit-tap-highlight-color:rgba(0,0,0,0)}body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.42857143;color:#333;background-color:#fff}input,button,select,textarea{font-family:inherit;font-size:inherit;line-height:inherit}a{color:#337ab7;text-decoration:none}a:hover,a:focus{color:#23527c;text-decoration:underline}a:focus{outline:5px auto -webkit-focus-ring-color;outline-offset:-2px}figure{margin:0}img{vertical-align:middle}.img-responsive{display:block;max-width:100%;height:auto}.img-rounded{border-radius:6px}.img-thumbnail{padding:4px;line-height:1.42857143;background-color:#fff;border:1px solid #ddd;border-radius:4px;-webkit-transition:all .2s ease-in-out;-o-transition:all .2s ease-in-out;transition:all .2s ease-in-out;display:inline-block;max-width:100%;height:auto}.img-circle{border-radius:50%}hr{margin-top:20px;margin-bottom:20px;border:0;border-top:1px solid #eee}.sr-only{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0, 0, 0, 0);border:0}.sr-only-focusable:active,.sr-only-focusable:focus{position:static;width:auto;height:auto;margin:0;overflow:visible;clip:auto}[role="button"]{cursor:pointer}h1,h2,h3,h4,h5,h6,.h1,.h2,.h3,.h4,.h5,.h6{font-family:inherit;font-weight:500;line-height:1.1;color:inherit}h1 small,h2 small,h3 small,h4 small,h5 small,h6 small,.h1 small,.h2 small,.h3 small,.h4 small,.h5 small,.h6 small,h1 .small,h2 .small,h3 .small,h4 .small,h5 .small,h6 .small,.h1 .small,.h2 .small,.h3 .small,.h4 .small,.h5 .small,.h6 .small{font-weight:normal;line-height:1;color:#777}h1,.h1,h2,.h2,h3,.h3{margin-top:20px;margin-bottom:10px}h1 small,.h1 small,h2 small,.h2 small,h3 small,.h3 small,h1 .small,.h1 .small,h2 .small,.h2 .small,h3 .small,.h3 .small{font-size:65%}h4,.h4,h5,.h5,h6,.h6{margin-top:10px;margin-bottom:10px}h4 small,.h4 small,h5 small,.h5 small,h6 small,.h6 small,h4 .small,.h4 .small,h5 .small,.h5 .small,h6 .small,.h6 .small{font-size:75%}h1,.h1{font-size:36px}h2,.h2{font-size:30px}h3,.h3{font-size:24px}h4,.h4{font-size:18px}h5,.h5{font-size:14px}h6,.h6{font-size:12px}p{margin:0 0 10px}.lead{margin-bottom:20px;font-size:16px;font-weight:300;line-height:1.4}@media (min-width:768px){.lead{font-size:21px}}small,.small{font-size:85%}mark,.mark{background-color:#fcf8e3;padding:.2em}.text-left{text-align:left}.text-right{text-align:right}.text-center{text-align:center}.text-justify{text-align:justify}.text-nowrap{white-space:nowrap}.text-lowercase{text-transform:lowercase}.text-uppercase{text-transform:uppercase}.text-capitalize{text-transform:capitalize}.text-muted{color:#777}.text-primary{color:#337ab7}a.text-primary:hover,a.text-primary:focus{color:#286090}.text-success{color:#3c763d}a.text-success:hover,a.text-success:focus{color:#2b542c}.text-info{color:#31708f}a.text-info:hover,a.text-info:focus{color:#245269}.text-warning{color:#8a6d3b}a.text-warning:hover,a.text-warning:focus{color:#66512c}.text-danger{color:#a94442}a.text-danger:hover,a.text-danger:focus{color:#843534}.bg-primary{color:#fff;background-color:#337ab7}a.bg-primary:hover,a.bg-primary:focus{background-color:#286090}.bg-success{background-color:#dff0d8}a.bg-success:hover,a.bg-success:focus{background-color:#c1e2b3}.bg-info{background-color:#d9edf7}a.bg-info:hover,a.bg-info:focus{background-color:#afd9ee}.bg-warning{background-color:#fcf8e3}a.bg-warning:hover,a.bg-warning:focus{background-color:#f7ecb5}.bg-danger{background-color:#f2dede}a.bg-danger:hover,a.bg-danger:focus{background-color:#e4b9b9}.page-header{padding-bottom:9px;margin:40px 0 20px;border-bottom:1px solid #eee}ul,ol{margin-top:0;margin-bottom:10px}ul ul,ol ul,ul ol,ol ol{margin-bottom:0}.list-unstyled{padding-left:0;list-style:none}.list-inline{padding-left:0;list-style:none;margin-left:-5px}.list-inline>li{display:inline-block;padding-left:5px;padding-right:5px}dl{margin-top:0;margin-bottom:20px}dt,dd{line-height:1.42857143}dt{font-weight:bold}dd{margin-left:0}@media (min-width:768px){.dl-horizontal dt{float:left;width:160px;clear:left;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.dl-horizontal dd{margin-left:180px}}abbr[title],abbr[data-original-title]{cursor:help;border-bottom:1px dotted #777}.initialism{font-size:90%;text-transform:uppercase}blockquote{padding:10px 20px;margin:0 0 20px;font-size:17.5px;border-left:5px solid #eee}blockquote p:last-child,blockquote ul:last-child,blockquote ol:last-child{margin-bottom:0}blockquote footer,blockquote small,blockquote .small{display:block;font-size:80%;line-height:1.42857143;color:#777}blockquote footer:before,blockquote small:before,blockquote .small:before{content:'\2014 \00A0'}.blockquote-reverse,blockquote.pull-right{padding-right:15px;padding-left:0;border-right:5px solid #eee;border-left:0;text-align:right}.blockquote-reverse footer:before,blockquote.pull-right footer:before,.blockquote-reverse small:before,blockquote.pull-right small:before,.blockquote-reverse .small:before,blockquote.pull-right .small:before{content:''}.blockquote-reverse footer:after,blockquote.pull-right footer:after,.blockquote-reverse small:after,blockquote.pull-right small:after,.blockquote-reverse .small:after,blockquote.pull-right .small:after{content:'\00A0 \2014'}address{margin-bottom:20px;font-style:normal;line-height:1.42857143}code,kbd,pre,samp{font-family:Menlo,Monaco,Consolas,"Courier New",monospace}code{padding:2px 4px;font-size:90%;color:#c7254e;background-color:#f9f2f4;border-radius:4px}kbd{padding:2px 4px;font-size:90%;color:#fff;background-color:#333;border-radius:3px;-webkit-box-shadow:inset 0 -1px 0 rgba(0,0,0,0.25);box-shadow:inset 0 -1px 0 rgba(0,0,0,0.25)}kbd kbd{padding:0;font-size:100%;font-weight:bold;-webkit-box-shadow:none;box-shadow:none}pre{display:block;padding:9.5px;margin:0 0 10px;font-size:13px;line-height:1.42857143;word-break:break-all;word-wrap:break-word;color:#333;background-color:#f5f5f5;border:1px solid #ccc;border-radius:4px}pre code{padding:0;font-size:inherit;color:inherit;white-space:pre-wrap;background-color:transparent;border-radius:0}.pre-scrollable{max-height:340px;overflow-y:scroll}.list-group{margin-bottom:20px;padding-left:0}.list-group-item{position:relative;display:block;padding:10px 15px;margin-bottom:-1px;background-color:#fff;border:1px solid #ddd}.list-group-item:first-child{border-top-right-radius:4px;border-top-left-radius:4px}.list-group-item:last-child{margin-bottom:0;border-bottom-right-radius:4px;border-bottom-left-radius:4px}a.list-group-item,button.list-group-item{color:#555}a.list-group-item .list-group-item-heading,button.list-group-item .list-group-item-heading{color:#333}a.list-group-item:hover,button.list-group-item:hover,a.list-group-item:focus,button.list-group-item:focus{text-decoration:none;color:#555;background-color:#f5f5f5}button.list-group-item{width:100%;text-align:left}.list-group-item.disabled,.list-group-item.disabled:hover,.list-group-item.disabled:focus{background-color:#eee;color:#777;cursor:not-allowed}.list-group-item.disabled .list-group-item-heading,.list-group-item.disabled:hover .list-group-item-heading,.list-group-item.disabled:focus .list-group-item-heading{color:inherit}.list-group-item.disabled .list-group-item-text,.list-group-item.disabled:hover .list-group-item-text,.list-group-item.disabled:focus .list-group-item-text{color:#777}.list-group-item.active,.list-group-item.active:hover,.list-group-item.active:focus{z-index:2;color:#fff;background-color:#337ab7;border-color:#337ab7}.list-group-item.active .list-group-item-heading,.list-group-item.active:hover .list-group-item-heading,.list-group-item.active:focus .list-group-item-heading,.list-group-item.active .list-group-item-heading>small,.list-group-item.active:hover .list-group-item-heading>small,.list-group-item.active:focus .list-group-item-heading>small,.list-group-item.active .list-group-item-heading>.small,.list-group-item.active:hover .list-group-item-heading>.small,.list-group-item.active:focus .list-group-item-heading>.small{color:inherit}.list-group-item.active .list-group-item-text,.list-group-item.active:hover .list-group-item-text,.list-group-item.active:focus .list-group-item-text{color:#c7ddef}.list-group-item-success{color:#3c763d;background-color:#dff0d8}a.list-group-item-success,button.list-group-item-success{color:#3c763d}a.list-group-item-success .list-group-item-heading,button.list-group-item-success .list-group-item-heading{color:inherit}a.list-group-item-success:hover,button.list-group-item-success:hover,a.list-group-item-success:focus,button.list-group-item-success:focus{color:#3c763d;background-color:#d0e9c6}a.list-group-item-success.active,button.list-group-item-success.active,a.list-group-item-success.active:hover,button.list-group-item-success.active:hover,a.list-group-item-success.active:focus,button.list-group-item-success.active:focus{color:#fff;background-color:#3c763d;border-color:#3c763d}.list-group-item-info{color:#31708f;background-color:#d9edf7}a.list-group-item-info,button.list-group-item-info{color:#31708f}a.list-group-item-info .list-group-item-heading,button.list-group-item-info .list-group-item-heading{color:inherit}a.list-group-item-info:hover,button.list-group-item-info:hover,a.list-group-item-info:focus,button.list-group-item-info:focus{color:#31708f;background-color:#c4e3f3}a.list-group-item-info.active,button.list-group-item-info.active,a.list-group-item-info.active:hover,button.list-group-item-info.active:hover,a.list-group-item-info.active:focus,button.list-group-item-info.active:focus{color:#fff;background-color:#31708f;border-color:#31708f}.list-group-item-warning{color:#8a6d3b;background-color:#fcf8e3}a.list-group-item-warning,button.list-group-item-warning{color:#8a6d3b}a.list-group-item-warning .list-group-item-heading,button.list-group-item-warning .list-group-item-heading{color:inherit}a.list-group-item-warning:hover,button.list-group-item-warning:hover,a.list-group-item-warning:focus,button.list-group-item-warning:focus{color:#8a6d3b;background-color:#faf2cc}a.list-group-item-warning.active,button.list-group-item-warning.active,a.list-group-item-warning.active:hover,button.list-group-item-warning.active:hover,a.list-group-item-warning.active:focus,button.list-group-item-warning.active:focus{color:#fff;background-color:#8a6d3b;border-color:#8a6d3b}.list-group-item-danger{color:#a94442;background-color:#f2dede}a.list-group-item-danger,button.list-group-item-danger{color:#a94442}a.list-group-item-danger .list-group-item-heading,button.list-group-item-danger .list-group-item-heading{color:inherit}a.list-group-item-danger:hover,button.list-group-item-danger:hover,a.list-group-item-danger:focus,button.list-group-item-danger:focus{color:#a94442;background-color:#ebcccc}a.list-group-item-danger.active,button.list-group-item-danger.active,a.list-group-item-danger.active:hover,button.list-group-item-danger.active:hover,a.list-group-item-danger.active:focus,button.list-group-item-danger.active:focus{color:#fff;background-color:#a94442;border-color:#a94442}.list-group-item-heading{margin-top:0;margin-bottom:5px}.list-group-item-text{margin-bottom:0;line-height:1.3}.panel{margin-bottom:20px;background-color:#fff;border:1px solid transparent;border-radius:4px;-webkit-box-shadow:0 1px 1px rgba(0,0,0,0.05);box-shadow:0 1px 1px rgba(0,0,0,0.05)}.panel-body{padding:15px}.panel-heading{padding:10px 15px;border-bottom:1px solid transparent;border-top-right-radius:3px;border-top-left-radius:3px}.panel-heading>.dropdown .dropdown-toggle{color:inherit}.panel-title{margin-top:0;margin-bottom:0;font-size:16px;color:inherit}.panel-title>a,.panel-title>small,.panel-title>.small,.panel-title>small>a,.panel-title>.small>a{color:inherit}.panel-footer{padding:10px 15px;background-color:#f5f5f5;border-top:1px solid #ddd;border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel>.list-group,.panel>.panel-collapse>.list-group{margin-bottom:0}.panel>.list-group .list-group-item,.panel>.panel-collapse>.list-group .list-group-item{border-width:1px 0;border-radius:0}.panel>.list-group:first-child .list-group-item:first-child,.panel>.panel-collapse>.list-group:first-child .list-group-item:first-child{border-top:0;border-top-right-radius:3px;border-top-left-radius:3px}.panel>.list-group:last-child .list-group-item:last-child,.panel>.panel-collapse>.list-group:last-child .list-group-item:last-child{border-bottom:0;border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel>.panel-heading+.panel-collapse>.list-group .list-group-item:first-child{border-top-right-radius:0;border-top-left-radius:0}.panel-heading+.list-group .list-group-item:first-child{border-top-width:0}.list-group+.panel-footer{border-top-width:0}.panel>.table,.panel>.table-responsive>.table,.panel>.panel-collapse>.table{margin-bottom:0}.panel>.table caption,.panel>.table-responsive>.table caption,.panel>.panel-collapse>.table caption{padding-left:15px;padding-right:15px}.panel>.table:first-child,.panel>.table-responsive:first-child>.table:first-child{border-top-right-radius:3px;border-top-left-radius:3px}.panel>.table:first-child>thead:first-child>tr:first-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child,.panel>.table:first-child>tbody:first-child>tr:first-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child{border-top-left-radius:3px;border-top-right-radius:3px}.panel>.table:first-child>thead:first-child>tr:first-child td:first-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child td:first-child,.panel>.table:first-child>tbody:first-child>tr:first-child td:first-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child td:first-child,.panel>.table:first-child>thead:first-child>tr:first-child th:first-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child th:first-child,.panel>.table:first-child>tbody:first-child>tr:first-child th:first-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child th:first-child{border-top-left-radius:3px}.panel>.table:first-child>thead:first-child>tr:first-child td:last-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child td:last-child,.panel>.table:first-child>tbody:first-child>tr:first-child td:last-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child td:last-child,.panel>.table:first-child>thead:first-child>tr:first-child th:last-child,.panel>.table-responsive:first-child>.table:first-child>thead:first-child>tr:first-child th:last-child,.panel>.table:first-child>tbody:first-child>tr:first-child th:last-child,.panel>.table-responsive:first-child>.table:first-child>tbody:first-child>tr:first-child th:last-child{border-top-right-radius:3px}.panel>.table:last-child,.panel>.table-responsive:last-child>.table:last-child{border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel>.table:last-child>tbody:last-child>tr:last-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child,.panel>.table:last-child>tfoot:last-child>tr:last-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child{border-bottom-left-radius:3px;border-bottom-right-radius:3px}.panel>.table:last-child>tbody:last-child>tr:last-child td:first-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child td:first-child,.panel>.table:last-child>tfoot:last-child>tr:last-child td:first-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child td:first-child,.panel>.table:last-child>tbody:last-child>tr:last-child th:first-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child th:first-child,.panel>.table:last-child>tfoot:last-child>tr:last-child th:first-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child th:first-child{border-bottom-left-radius:3px}.panel>.table:last-child>tbody:last-child>tr:last-child td:last-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child td:last-child,.panel>.table:last-child>tfoot:last-child>tr:last-child td:last-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child td:last-child,.panel>.table:last-child>tbody:last-child>tr:last-child th:last-child,.panel>.table-responsive:last-child>.table:last-child>tbody:last-child>tr:last-child th:last-child,.panel>.table:last-child>tfoot:last-child>tr:last-child th:last-child,.panel>.table-responsive:last-child>.table:last-child>tfoot:last-child>tr:last-child th:last-child{border-bottom-right-radius:3px}.panel>.panel-body+.table,.panel>.panel-body+.table-responsive,.panel>.table+.panel-body,.panel>.table-responsive+.panel-body{border-top:1px solid #ddd}.panel>.table>tbody:first-child>tr:first-child th,.panel>.table>tbody:first-child>tr:first-child td{border-top:0}.panel>.table-bordered,.panel>.table-responsive>.table-bordered{border:0}.panel>.table-bordered>thead>tr>th:first-child,.panel>.table-responsive>.table-bordered>thead>tr>th:first-child,.panel>.table-bordered>tbody>tr>th:first-child,.panel>.table-responsive>.table-bordered>tbody>tr>th:first-child,.panel>.table-bordered>tfoot>tr>th:first-child,.panel>.table-responsive>.table-bordered>tfoot>tr>th:first-child,.panel>.table-bordered>thead>tr>td:first-child,.panel>.table-responsive>.table-bordered>thead>tr>td:first-child,.panel>.table-bordered>tbody>tr>td:first-child,.panel>.table-responsive>.table-bordered>tbody>tr>td:first-child,.panel>.table-bordered>tfoot>tr>td:first-child,.panel>.table-responsive>.table-bordered>tfoot>tr>td:first-child{border-left:0}.panel>.table-bordered>thead>tr>th:last-child,.panel>.table-responsive>.table-bordered>thead>tr>th:last-child,.panel>.table-bordered>tbody>tr>th:last-child,.panel>.table-responsive>.table-bordered>tbody>tr>th:last-child,.panel>.table-bordered>tfoot>tr>th:last-child,.panel>.table-responsive>.table-bordered>tfoot>tr>th:last-child,.panel>.table-bordered>thead>tr>td:last-child,.panel>.table-responsive>.table-bordered>thead>tr>td:last-child,.panel>.table-bordered>tbody>tr>td:last-child,.panel>.table-responsive>.table-bordered>tbody>tr>td:last-child,.panel>.table-bordered>tfoot>tr>td:last-child,.panel>.table-responsive>.table-bordered>tfoot>tr>td:last-child{border-right:0}.panel>.table-bordered>thead>tr:first-child>td,.panel>.table-responsive>.table-bordered>thead>tr:first-child>td,.panel>.table-bordered>tbody>tr:first-child>td,.panel>.table-responsive>.table-bordered>tbody>tr:first-child>td,.panel>.table-bordered>thead>tr:first-child>th,.panel>.table-responsive>.table-bordered>thead>tr:first-child>th,.panel>.table-bordered>tbody>tr:first-child>th,.panel>.table-responsive>.table-bordered>tbody>tr:first-child>th{border-bottom:0}.panel>.table-bordered>tbody>tr:last-child>td,.panel>.table-responsive>.table-bordered>tbody>tr:last-child>td,.panel>.table-bordered>tfoot>tr:last-child>td,.panel>.table-responsive>.table-bordered>tfoot>tr:last-child>td,.panel>.table-bordered>tbody>tr:last-child>th,.panel>.table-responsive>.table-bordered>tbody>tr:last-child>th,.panel>.table-bordered>tfoot>tr:last-child>th,.panel>.table-responsive>.table-bordered>tfoot>tr:last-child>th{border-bottom:0}.panel>.table-responsive{border:0;margin-bottom:0}.panel-group{margin-bottom:20px}.panel-group .panel{margin-bottom:0;border-radius:4px}.panel-group .panel+.panel{margin-top:5px}.panel-group .panel-heading{border-bottom:0}.panel-group .panel-heading+.panel-collapse>.panel-body,.panel-group .panel-heading+.panel-collapse>.list-group{border-top:1px solid #ddd}.panel-group .panel-footer{border-top:0}.panel-group .panel-footer+.panel-collapse .panel-body{border-bottom:1px solid #ddd}.panel-default{border-color:#ddd}.panel-default>.panel-heading{color:#333;background-color:#f5f5f5;border-color:#ddd}.panel-default>.panel-heading+.panel-collapse>.panel-body{border-top-color:#ddd}.panel-default>.panel-heading .badge{color:#f5f5f5;background-color:#333}.panel-default>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#ddd}.panel-primary{border-color:#337ab7}.panel-primary>.panel-heading{color:#fff;background-color:#337ab7;border-color:#337ab7}.panel-primary>.panel-heading+.panel-collapse>.panel-body{border-top-color:#337ab7}.panel-primary>.panel-heading .badge{color:#337ab7;background-color:#fff}.panel-primary>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#337ab7}.panel-success{border-color:#d6e9c6}.panel-success>.panel-heading{color:#3c763d;background-color:#dff0d8;border-color:#d6e9c6}.panel-success>.panel-heading+.panel-collapse>.panel-body{border-top-color:#d6e9c6}.panel-success>.panel-heading .badge{color:#dff0d8;background-color:#3c763d}.panel-success>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#d6e9c6}.panel-info{border-color:#bce8f1}.panel-info>.panel-heading{color:#31708f;background-color:#d9edf7;border-color:#bce8f1}.panel-info>.panel-heading+.panel-collapse>.panel-body{border-top-color:#bce8f1}.panel-info>.panel-heading .badge{color:#d9edf7;background-color:#31708f}.panel-info>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#bce8f1}.panel-warning{border-color:#faebcc}.panel-warning>.panel-heading{color:#8a6d3b;background-color:#fcf8e3;border-color:#faebcc}.panel-warning>.panel-heading+.panel-collapse>.panel-body{border-top-color:#faebcc}.panel-warning>.panel-heading .badge{color:#fcf8e3;background-color:#8a6d3b}.panel-warning>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#faebcc}.panel-danger{border-color:#ebccd1}.panel-danger>.panel-heading{color:#a94442;background-color:#f2dede;border-color:#ebccd1}.panel-danger>.panel-heading+.panel-collapse>.panel-body{border-top-color:#ebccd1}.panel-danger>.panel-heading .badge{color:#f2dede;background-color:#a94442}.panel-danger>.panel-footer+.panel-collapse>.panel-body{border-bottom-color:#ebccd1}.clearfix:before,.clearfix:after,.dl-horizontal dd:before,.dl-horizontal dd:after,.panel-body:before,.panel-body:after{content:" ";display:table}.clearfix:after,.dl-horizontal dd:after,.panel-body:after{clear:both}.center-block{display:block;margin-left:auto;margin-right:auto}.pull-right{float:right !important}.pull-left{float:left !important}.hide{display:none !important}.show{display:block !important}.invisible{visibility:hidden}.text-hide{font:0/0 a;color:transparent;text-shadow:none;background-color:transparent;border:0}.hidden{display:none !important}.affix{position:fixed}
  </style>
</head>
<body>
  <h1>Query: {{title}} </h1>
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


def html_report(title, records):
    html = template.render(
        title=title, 
        header_fields=header_fields, 
        footer_fields=footer_fields,
        records=records
    )
    return html

def pdf_report(title, records):
    html = html_report(title, records)
    pdf  = pdfkit.from_string(html, False)
    return pdf


if __name__ == "__main__":
    def main():
        with open("/tmp/example.html", "wt") as fp:
            fp.write(html_report(title, records))
        with open("/tmp/example.pdf", "wb") as fp:
            fp.write(pdf_report(title, records))
        print("DONE")

    title = "Test report"
    null = None
    records = [
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "None",
            "userdata3": "Old md5sum: 714b8dd04e465c645a94d724843911ad",
            "filename": "/etc/init.d/.depend.start",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:21:34.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9011e6-9a51-000c-2974-c87af7b1f68c",
            "ossim_reliability": 1,
            "userdata4": "New sha1sum: ffa2e1fbdd11f1928505513ab8284b953af37804",
            "userdata2": "New md5sum: d7e4d3108a17230a85f4c8cc4c3b01a6",
            "_id": "57f7a5d0a4afb66be0433b00",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "Old sha1sum: dd9d026b749be5061c5bf21d4a4cdb4df623beef",
            "userdata6": "Old size: 3687",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "New size: 3768",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7094,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846494\" --> RID: \"552\"; RL: \"7\"; RG: \"ossec,syscheck,\"; RC: \"Integrity checksum changed again (3rd time).\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"syscheck\"; EVENT: \"[INIT]Integrity checksum changed for: '/etc/init.d/.depend.start'\\nSize changed from '3687' to '3768'\\nOld md5sum was: '714b8dd04e465c645a94d724843911ad'\\nNew md5sum is : 'd7e4d3108a17230a85f4c8cc4c3b01a6'\\nOld sha1sum was: 'dd9d026b749be5061c5bf21d4a4cdb4df623beef'\\nNew sha1sum is : 'ffa2e1fbdd11f1928505513ab8284b953af37804'\\n[END]\"; ",
            "plugin_sid": 552,
            "tzone": 0
        },
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "None",
            "userdata3": "Old md5sum: a25382fede268523fc2f8784682817ae",
            "filename": "/etc/init.d/.depend.stop",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:21:38.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9011e6-9a51-000c-2974-c87afa1a050e",
            "ossim_reliability": 1,
            "userdata4": "New sha1sum: 275a077766bf0615b8fa243ea8eed48e3eb11a59",
            "userdata2": "New md5sum: 636c43b5e58c4d5fe0c886e2eccd4a0b",
            "_id": "57f7a5d0a4afb66be0433b01",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "Old sha1sum: d9b96549a55e9aef445426c6eb8194aaa548528d",
            "userdata6": "Old size: 3079",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "New size: 3149",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7094,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846498\" --> RID: \"550\"; RL: \"7\"; RG: \"ossec,syscheck,\"; RC: \"Integrity checksum changed.\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"syscheck\"; EVENT: \"[INIT]Integrity checksum changed for: '/etc/init.d/.depend.stop'\\nSize changed from '3079' to '3149'\\nOld md5sum was: 'a25382fede268523fc2f8784682817ae'\\nNew md5sum is : '636c43b5e58c4d5fe0c886e2eccd4a0b'\\nOld sha1sum was: 'd9b96549a55e9aef445426c6eb8194aaa548528d'\\nNew sha1sum is : '275a077766bf0615b8fa243ea8eed48e3eb11a59'\\n[END]\"; ",
            "plugin_sid": 550,
            "tzone": 0
        },
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "root",
            "userdata3": "pam,syslog,",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:23:04.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a2d55c746",
            "ossim_reliability": 1,
            "userdata4": "none",
            "userdata2": "Login session closed.",
            "_id": "57f7a5d0a4afb66be0433b02",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7001,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846584\" --> RID: \"5502\"; RL: \"3\"; RG: \"pam,syslog,\"; RC: \"Login session closed.\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:23:03 alienvault sshd[4610]: pam_unix(sshd:session): session closed for user root[END]\"; ",
            "plugin_sid": 5502,
            "tzone": 0
        },
        {
            "src_net": null,
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "root",
            "userdata3": "SSHD authentication success.",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 36778,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:23:14.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": null,
            "ip_src": "10.105.1.209",
            "src_hostname": "",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a334c985a",
            "ossim_reliability": 1,
            "userdata4": "syslog,sshd,authentication_success,",
            "userdata2": "10.105.1.209",
            "_id": "57f7a5d0a4afb66be0433b03",
            "ossim_correlation": 1,
            "src_host": null,
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7009,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846594\" --> RID: \"5715\"; RL: \"3\"; RG: \"syslog,sshd,authentication_success,\"; RC: \"SSHD authentication success.\"; USER: \"None\"; SRCIP: \"10.105.1.209\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:23:13 alienvault sshd[5848]: Accepted password for root from 10.105.1.209 port 36778 ssh2[END]\"; ",
            "plugin_sid": 5715,
            "tzone": 0
        },
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "root",
            "userdata3": "pam,syslog,authentication_success,",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:23:14.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a334ce288",
            "ossim_reliability": 1,
            "userdata4": "none",
            "userdata2": "Login session opened.",
            "_id": "57f7a5d0a4afb66be0433b04",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7009,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846594\" --> RID: \"5501\"; RL: \"3\"; RG: \"pam,syslog,authentication_success,\"; RC: \"Login session opened.\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:23:13 alienvault sshd[5848]: pam_unix(sshd:session): session opened for user root by (uid=0)[END]\"; ",
            "plugin_sid": 5501,
            "tzone": 0
        },
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "tunnel",
            "userdata3": "syslog,adduser",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": null,
            "timestamp": "2016-10-07 13:23:42.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a4416d998",
            "ossim_reliability": 1,
            "userdata4": "",
            "userdata2": "8",
            "_id": "57f7a5d0a4afb66be0433b05",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": null,
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7032,
            "dst_mac": null,
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "",
            "ip_dst": "0.0.0.0",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846622\" --> RID: \"5901\"; RL: \"8\"; RG: \"syslog,adduser\"; RC: \"New group added to the system\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:23:41 alienvault useradd[5949]: new group: name=tunnel, GID=1003[END]\"; ",
            "plugin_sid": 5901,
            "tzone": 0
        },
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "tunnel",
            "userdata3": "syslog,adduser",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": null,
            "timestamp": "2016-10-07 13:23:42.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a44172bfa",
            "ossim_reliability": 1,
            "userdata4": "",
            "userdata2": "8",
            "_id": "57f7a5d0a4afb66be0433b06",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": null,
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7032,
            "dst_mac": null,
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "",
            "ip_dst": "0.0.0.0",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846622\" --> RID: \"5902\"; RL: \"8\"; RG: \"syslog,adduser\"; RC: \"New user added to the system\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:23:41 alienvault useradd[5949]: new user: name=tunnel, UID=1003, GID=1003, home=/home/tunnel, shell=/bin/false[END]\"; ",
            "plugin_sid": 5902,
            "tzone": 0
        },
        {
            "src_net": null,
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "tunnel",
            "userdata3": "pam,syslog,",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:23:44.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": null,
            "ip_src": "0.0.0.0",
            "src_hostname": "",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a4548c39e",
            "ossim_reliability": 1,
            "userdata4": "",
            "userdata2": "User changed password.",
            "_id": "57f7a5d0a4afb66be0433b07",
            "ossim_correlation": 1,
            "src_host": null,
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7001,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846624\" --> RID: \"5555\"; RL: \"3\"; RG: \"pam,syslog,\"; RC: \"User changed password.\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:23:42 alienvault passwd[5958]: pam_unix(passwd:chauthtok): password changed for tunnel[END]\"; ",
            "plugin_sid": 5555,
            "tzone": 0
        },
        {
            "src_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "root",
            "userdata3": "pam,syslog,",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:24:10.000000",
            "ossim_priority": 1,
            "ossim_risk_c": 0,
            "src_mac": "00:0c:29:76:1d:9a",
            "ip_src": "192.168.2.1",
            "src_hostname": "alienvault",
            "ip_proto": 6,
            "id": "8c9111e6-9a51-000c-2974-c87a54cb28c0",
            "ossim_reliability": 1,
            "userdata4": "none",
            "userdata2": "Login session closed.",
            "_id": "57f7a5d0a4afb66be0433b08",
            "ossim_correlation": 1,
            "src_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 7001,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "/var/log/auth.log",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "AV - Alert - \"1475846650\" --> RID: \"5502\"; RL: \"3\"; RG: \"pam,syslog,\"; RC: \"Login session closed.\"; USER: \"None\"; SRCIP: \"None\"; HOSTNAME: \"alienvault\"; LOCATION: \"/var/log/auth.log\"; EVENT: \"[INIT]Oct    7 15:24:09 alienvault sshd[5848]: pam_unix(sshd:session): session closed for user root[END]\"; ",
            "plugin_sid": 5502,
            "tzone": 0
        },
        {
            "src_net": null,
            "userdata8": "",
            "password": "",
            "ossim_risk_a": 0,
            "binary_data": null,
            "username": "tunnel",
            "userdata3": "",
            "filename": "",
            "layer4_dport": 0,
            "layer4_sport": 0,
            "dst_net": "6a53:6186:a656:acc6:c239:c199:5d19:575d",
            "timestamp": "2016-10-07 13:23:41.000000",
            "ossim_priority": 3,
            "ossim_risk_c": 0,
            "src_mac": null,
            "ip_src": "0.0.0.0",
            "src_hostname": "",
            "ip_proto": 6,
            "id": "8c9111e6-9b56-000c-2974-c87a43a5de78",
            "ossim_reliability": 2,
            "userdata4": "",
            "userdata2": "",
            "_id": "57f7a5d0a4afb66be0433b09",
            "ossim_correlation": 1,
            "src_host": null,
            "userdata5": "",
            "userdata6": "",
            "batch_name": "/var/ossim/archives/2016_10_07_14_40_32",
            "userdata7": "",
            "dst_host": "e4ea:2182:32f5:11e6:90b6:3ab6:e041:a67a",
            "ossim_asset_src": 2,
            "ctx": "a1824f20-32f5-11e6-90b6-3ab6e041a67a",
            "ossim_asset_dst": 2,
            "plugin_id": 4004,
            "dst_mac": "00:0c:29:76:1d:9a",
            "userdata1": "useradd",
            "dst_hostname": "alienvault",
            "ip_dst": "192.168.2.1",
            "device_id": 1,
            "userdata9": "",
            "data_payload": "Oct    7 15:23:41 alienvault useradd[5949]: new group: name=tunnel, GID=1003 ",
            "plugin_sid": 5,
            "tzone": 0
        }
    ]
    main()