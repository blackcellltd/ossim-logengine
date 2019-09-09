#!/bin/bash

if [ -f /var/run/ossim-loguploader.pid ] &&
   [ kill -0 $(cat /var/run/ossim-loguploader.pid) ]; then
    return 0;
else
    /etc/init.d/ossim-loguploader start
fi
           
                                                
