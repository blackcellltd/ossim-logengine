# OSSIM-Logengine
Long term log storage extension for OSSIM (Open Source Security Incident Management), AlienVault
# Description

The basic architecture of the system can be seen on ossim-logengine_basic_architecture.jpg. The diagram shows the optimal case, where the main Ossim and the logarchiver are on different computers. The Ossim system is presumed to contain, at least, the base Ossim runtime, with a webserver, and the dashboard included, and also a MySQL database, containing the Ossim event records. The logserver component is set up to contain the Ossim logserver component, including a Tornado based web server, and the archiver scripts, and also a MongoDB runtime, to hold the collected data. As ossim-logengine_basic_architecture.jpg shows, the main communication between the two systems takes place through two component. First, the archiver on the logserver side queries the MySQL found at the Ossim side. The queried records are then reformatted, parsed, and stored in the MongoDB. The second connection is through the web servers. The Ossim dashboard loads the custom plugin, which grants access to the logarchive. The system is set up in a way, that the Tornado server on the logserver side only accepts queries from the specific dashboard page, created for this use-case. The dashboard page queries an API endpoint found on the logserver side, which in response queries the MongoDB. The requested records are then returned to the dashboard page, where a dynamically working Angular page deserializes them from JSON, and displays them for human usage.


# Dependencies

- tornado 4.3 for running the server and managing the file uploads.
- configobj 4.7.2 for parsing the configuration files.
- pymongo 4.7.2 for parsing the configuration files.
- pdfkit to generate pdf from python.
- wkhtmltopdf command line utility, pdfkit dependency.
- jinja2 HTML report generaton.
- pprint used in report generation.
- sqlalchemy 1.0.9 for querying the MySQL.
- sshtunnel 0.0.8.2 for creating an sshtunnel to the MySQL server.
- pymongo 3.2.2 for interacting with MongoDB.

# Installation

Installing ossim-logarchiver (ossim-additions)

- Log in to OSSIM 
- select "Jailbreak System" from the menu, then Yes
- Optional time synchronization, two methods (ntpdate or tlsdate)

- copy ossim-additions folder to /opt
- cd /opt/ossim-additions/
- edit install.sh, put server IP and port (default 4343)
- run install.sh
- copy/save the generated password! it will be needed later



# Troubleshooting
