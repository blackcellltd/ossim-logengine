#!/usr/bin/env python

lst = ['/logarchive/components/normalize-css/normalize.css',                
'/logarchive/components/angular/angular-csp.css',                    
'/logarchive/components/angular-bootstrap/ui-bootstrap-csp.css',     
'/logarchive/components/bootstrap/dist/css/bootstrap.css',           
'/logarchive/components/bootstrap/dist/css/bootstrap-theme.css',     
'/logarchive/css/logarchive.css']           

outf = open("all.css","wb")
for f in lst:
	with open(f, "rb") as css:
			outf.write(css.read())
outf.close()
