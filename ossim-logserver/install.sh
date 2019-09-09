#!/bin/bash

set +H

EMAIL="admin@example.com"
WEBPORT="4343"
SERVER_USER="archiveuser"
SERVERNAME=192.168.1.1
PORT=8888
DB_PATH=/var/lib/ossim_db
LOG_PATH=/var/log/ossim
ARCHIVE_PATH=/var/ossim/archives
INSTALL_DIR=/usr/share/python/ossim-logserver
CWD=`pwd`

if [ "${BASH_SOURCE%/*}" != "." ]; then
    echo "Please cd into the script directory first! (./install.sh should be the command)"
    exit 1
fi

if [ ! `id -u` -eq 0 ]; then
    echo "You must be root in order to run this script."
    exit 1
fi

# cd to install script folder
cd $CWD

useradd archiveuser

# Create config folder
mkdir -p /etc/ossim/
mkdir -p $LOG_PATH
mkdir -p /var/ossim
mkdir -p $ARCHIVE_PATH
chown -R $SERVER_USER:$SERVER_USER $LOG_PATH
chown -R $SERVER_USER:$SERVER_USER $ARCHIVE_PATH

# Import key and set up mongodb repo
echo "Setting up mongodb community repo..."
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927 > /dev/null 2>&1
echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main" | tee /etc/apt/sources.list.d/mongodb-org-3.2.list > /dev/null 2>&1
apt-get -qq update

# Install deps
echo "Installing dependencies..."
apt-get -qq --force-yes install python3 python3-pip mongodb-org nginx ntpdate libssl-dev libffi-dev gcc python3-dev wkhtmltopdf xvfb xauth

if [ $? -eq 0 ]; then
    echo "Dependencies installed."
else
    echo "Dependencies could not be installed! Try apt-get install python3 python3-pip mongodb-org nginx ntpdate libssl-dev lbffi-dev"
    exit 1
fi

echo "Replacing wkhtmltopdf with wrapper..."
mv /usr/bin/wkhtmltopdf /usr/bin/wkhtmltopdf-amd64
cp ./wkhtmltopdf-wrapper /usr/bin/wkhtmltopdf
chmod +rx /usr/bin/wkhtmltopdf
echo "Wrapper installed"

ntpdate -s time.nist.gov

echo "Installing Python dependencies..."
pip3 -q install tornado pymongo configobj pycrypto sqlalchemy sshtunnel pymysql dateutils pdfkit jinja2
if [ $? -eq 0 ]; then
    echo "Python dependencies installed."
else
    echo "Python dependencies could not be installed! Try pip3 install tornado pymongo configobj pycrypto sqlalchemy sshtunnel pymysql dateutil"
    exit 1
fi

echo "Fixing permissions..."
chmod -R +x /usr/local/lib/python3.4/dist-packages/jinja2
chmod -R +x /usr/local/lib/python3.4/dist-packages/pdfkit
echo "Permissions fixed"

echo "Copying configuration files..."
# Install init script and sanity check script
sed -re "s|!WEBPORT!|$WEBPORT|g" -i ./config/etc/nginx/sites-enabled/tornado
sed -re "s|!SERVERNAME!|$SERVERNAME|g" -i ./config/etc/nginx/sites-enabled/tornado
sed -re "s|!PORT!|$PORT|g" -i ./config/etc/nginx/sites-enabled/tornado
sed -re "s|!USER!|$SERVER_USER|g" -i ./config/etc/init.d/ossim-logserver
sed -re "s|!EMAIL!|$EMAIL|g" -i ./config/etc/monit/monitrc_append 

rm /etc/nginx/sites-enabled/default
cp -r ./config/etc /

chmod +x /etc/init.d/ossim-logserver
chmod +x /etc/cron.hourly/check-logserver.sh
echo "Configuration files copied and permissions set."

# Create a user
useradd -U $SERVER_USER

# Install actual program
echo "Installing ossim-logserver..."
mkdir -p $INSTALL_DIR
cp ossim_logserver.py ossim_logutilities.py timestamp_query.py ossim_sql_archiver.py $INSTALL_DIR
chown -R $SERVER_USER:$SERVER_USER $INSTALL_DIR
chmod +x $INSTALL_DIR/ossim_logserver.py
ln -s $INSTALL_DIR/ossim_logserver.py /usr/bin/ossim-logserver
echo "ossim-logserver is now installed."

# Create DB folder
echo "Configuring mongoDB"
mkdir -p $DB_PATH
chmod -R 774 $DB_PATH
chown -R root:mongodb $DB_PATH

# Change the DB folder to the one we created, change port
sed -re "s|(dbPath:\s?).*|\1$DB_PATH|g" -i /etc/mongod.conf
echo "Database path set to $DB_PATH"
sed -re "s|\#(port:\s?).*|\1$PORT|g" -i /etc/mongod.conf
echo "Database will be serving at port $PORT"

# Set mongod and logserver to autostart, start mongodb
update-rc.d mongod defaults
/etc/init.d/mongod start
update-rc.d ossim-logserver defaults
update-rc.d nginx defaults
echo "Logserver and database set to autostart"

# Default setup for mongo
chmod +x mongodb_setup.py
./mongodb_setup.py -c /etc/ossim/logserver.conf
if [ $? -eq 0 ]; then
    echo "MongoDB base configuration successfully completed."
else
    echo "MongoDB base configuration was unsuccessful. Try running ./mongodb_setup.py -c /etc/ossim/logserver.conf"
    exit 1
fi

# Default setup for mysql
chmod +x ossim_mysql_setup.py
./ossim_mysql_setup.py -c /etc/ossim/logserver.conf
if [ $? -eq 0 ]; then
    echo "MySQL base configuration successfully completed."
else
    echo "MySQL base configuration was unsuccessful. Try running ./ossim_mysql_setup.py -c /etc/ossim/logserver.conf"
    exit 1
fi

# Create the CA and server certs
echo "Generating CA and server certificates..."
mkdir -p /etc/nginx/ssl
mkdir -p ~/ssl && cd ~/ssl
echo "Generating CA private key (4096 bit). Grab a coffee, get comfy, this will take some time."
openssl genrsa -out rootCA.key 4096
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3285 -out rootCA.pem
echo "[!] Copy rootCA.pem to the servers containing the uploader. Please consult the documentation for the directory in which you must copy this certificate."
echo "Generating server private key (4096 bit). This will take equally as long as the previous key generation."
openssl genrsa -out server.key 4096
echo "[!] Fill out **COMMON NAME** with the domain name / address of this server. Also, make sure that the O/OU name is NOT the same as the CA's O/OU, it will show as a self-signed certificate elsewise!"
openssl req -new -key server.key -out server.csr
openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -days 3285 -sha256
openssl dhparam -dsaparam -out dhparam.pem 4096

cp dhparam.pem server.crt server.key /etc/nginx/ssl/
rm -f ./rootCA.key ./server.key ./server.crt

cd $CWD

echo "Starting services..."

/etc/init.d/nginx restart
/etc/init.d/ossim-logserver start
echo "Installing monit"
apt-get -qq install monit
cat ./config/etc/monit/monitrc_append >> /etc/monit/monitrc
monit reload
monit validate
update-rc.d monit defaults

echo "[!] Don't forget to copy the CA cert (~/ssl/rootCA.pem) to the OSSIM system, scp-ing as adminuser will put it in /home/adminuser (you don't need to do this on localhost)"
