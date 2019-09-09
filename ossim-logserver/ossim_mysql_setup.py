#!/usr/bin/env python3
import getopt
import uuid

import sqlalchemy
import getpass
import configobj
import sys
import paramiko
import time
import shutil
import sshtunnel
import subprocess

from Crypto import Random
from Crypto.Hash import SHA256
import logging

logging.basicConfig(filename="ossim_mysql_setup.log",
                    level="DEBUG",
                    format='[%(asctime)s] %(levelname)s: %(message)s')


def traceback_information(e_info):
    """
    Return a string containing traceback information about the recently happened exception.

    :param e_info: Output of sys.exc_info().
    :return : Loggable string containing traceback info, with filename, line number, exception type, message.
    """

    exc_type, exc_value, exc_traceback = e_info
    traceback = {
        'filename': exc_traceback.tb_frame.f_code.co_filename,
        'lineno': exc_traceback.tb_lineno,
        'name': exc_traceback.tb_frame.f_code.co_name,
        'type': exc_type.__name__,
        'message': str(exc_value)  # or see traceback._some_str()
    }

    del (exc_type, exc_value, exc_traceback)
    return 'Traceback: File "{filename}", line {lineno}, in {name}, {type}: {message}'.format(**traceback)


def read_config(config_file):
    """
    Read config file given in config_file argument, parse its body.

     In order for this script to work, the config file must contain at least:
     - A section called mysql.
     - In the section, the following keywords:
        - hostname: Hostname where the MySQL is accessible. If a tunnel_pwd is given, the script will try to use an ssh
    tunnel to this hostname.
        - port: Port where the MySQL is accessible. Same, if a tunnel_pwd is given, the script will try to tunnel to
    this port.

    - An optional keyword can be given in the mysql section: tunnel_pwd. Password of the tunnel user, if one is present
    on the server and should be used.

    For a detailed overview of the config file, see read_config in logserver.py.
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
                        "name": ""
                    }}

        required = {"archive_directory": None,
                    "server": [],
                    "mongo": ["database", "hostname", "port", "collection", "justinsert", "justread"],
                    "ossim": ["hostname", "port"]}

        parser = configobj.ConfigObj(config_file)
        all_predef_key = set(
            list(filter(lambda x: not x == "ossim", required)) + list(filter(lambda x: not x == "ossim", optional)))

        # All the keys that are not any of the already known keys.
        for key in filter(lambda x: x not in all_predef_key, parser.keys()):
            for subkey in required.get("ossim"):
                if subkey not in parser.get(key):
                    logging.error("{} not found in custom section {}!".format(subkey, key))
                    sys.exit(2)
            for subkey in optional.get("ossim"):
                if subkey not in parser.get(key):
                    parser.get(key)[subkey] = optional.get("ossim")[subkey]
                    logging.warning(
                        "The keyword {} was not found in custom section {}, defaulting to default value: {}".format(
                            subkey, key, optional["ossim"][subkey]))

        # for key in required:
        #     if parser.get(key, None) is None:
        #         key_type = "Section" if isinstance(required.get(key), dict) else "Keyword"
        #         logging.error("{} {} not found!".format(key_type, key))
        #         sys.exit(2)
        #     elif isinstance(required.get(key), list):
        #         for subkey in required[key]:
        #             if parser[key].get(subkey, None) is None:
        #                 logging.error("{} not found in section {}!".format(subkey, key))
        #                 sys.exit(2)
        #
        # for key in optional:
        #     if parser.get(key, None) is None:
        #         parser[key] = optional[key]
        #         logging.warning(
        #             "The keyword {} was not found, defaulting to default value: {}".format(key, optional[key]))
        #     elif isinstance(optional.get(key), dict):
        #         for subkey in optional[key]:
        #             if parser[key].get(subkey, None) is None:
        #                 parser[key][subkey] = optional[key][subkey]
        #                 logging.warning(
        #                     "The keyword {} was not found in section {}, defaulting to default value: {}".format(subkey,
        #                                                                                                          key,
        #                                                                                                          optional[
        #                                                                                                              key][
        #                                                                                                              subkey]))

        return parser, set(filter(lambda x : x not in all_predef_key,parser.keys()))

    except IOError:
        logging.error("Unable to read config file {configfile}!", configfile=parser.filename)
        sys.exit(2)
    except configobj.ParseError:
        logging.error("Error in config file {configfile} format!", configfile=parser.filename)


def rollback(config, ossim_key, use_ssh, mysql_username, mysql_password, was_error=True):
    """ Roll back every change made by this script.

    Deletes the logarchive database, drops the trigger created on alienvault_siem, and deletes ossim_logserver user.

    :param config: Config dictionary, read in by read_config
    :param username: Username for the MySQL server. The user must have permissions to create users, and grant privileges.
    :param password: Password for the aforementioned
    :param was_error: Boolean value to enable this function to be used through command line flags.
    """
    using_tunnel = False if config["mysql"]["tunnel_pwd"] == "" else True
    if was_error:
        cont = input("An error occured during the setup script, please see the logs. Do you want to rollback? (y/n) ")
        cont = True if cont.lower() == "y" else False
    else:
        cont = True
    if cont:
        if use_ssh:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            print("Now the script needs an ssh user who has shell access and can execute mysql commands.")
            ssh_username = input("Please enter the ssh username: ")
            ssh_password = getpass.getpass(prompt="Please enter the ssh password: ")
            ssh.connect(config[ossim_key]["hostname"], port=int(config[ossim_key]["port"]), username=ssh_username,
                        password=ssh_password)

            stdin, stdout, stderr = ssh.exec_command(
                'mysql -u{} -p{} -hlocalhost alienvault_siem -e"DROP DATABASE logarchive;Drop trigger alienvault_siem.id_copier;Drop user ossim_logserver@127.0.0.1;" '.format(
                    mysql_username, mysql_password))
        else:

            subprocess.call(["mysql", "-u{}".format(mysql_username), "-p{}".format(mysql_password), "-hlocalhost",
                             "alienvault_siem", "-e",
                             "DROP DATABASE logarchive;DROP TRIGGER alienvault_siem.id_copier;DROP USER ossim_logserver@127.0.0.1;"])


def setup(config, ossim_key, use_ssh, mysql_username, mysql_password):
    user_password = SHA256.new(Random.new().read(50)).hexdigest()
    shutil.copy("mysql_setup.sql","mysql_setup.sql.bak")
    subprocess.call(["sed", "-i", "s/USR_PW/{}/g".format(user_password), "mysql_setup.sql"])
    if use_ssh:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            print("Now the script needs an ssh user who has shell access and can execute mysql commands.")
            ssh_username = input("Please enter the ssh username: ")
            ssh_password = getpass.getpass(prompt="Please enter the ssh password: ")
            ssh.connect(config[ossim_key]["hostname"], port=int(config[ossim_key]["port"]), username=ssh_username,
                        password=ssh_password)

            sftp = ssh.open_sftp()
            sftp.put('mysql_setup.sql', './mysql_setup.sql')
            sftp.close()
            ssh.close()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(config[ossim_key]["hostname"], port=int(config[ossim_key]["port"]), username=ssh_username,
                        password=ssh_password)
            stdin, stdout, stderr = ssh.exec_command(
                'mysql -u{} -p{} -hlocalhost alienvault_siem -e"source mysql_setup.sql;" '.format(
                    mysql_username, mysql_password))
            logging.debug("Logging stdout,stderr of mysql command:")
            logging.debug("stdout: {}".format(stdout.read()))
            logging.debug("stderr: {}".format(stderr.read()))


        except Exception as e:
            logging.error("Unexpected error happened while running setup sql. {}".format(type(e)))
            logging.debug(traceback_information(sys.exc_info()))
        finally:
            ssh.close()
    else:
        try:
            base_command = ["mysql", "-u{}".format(mysql_username), "-p{}".format(mysql_password), "-hlocalhost",
                            "alienvault_siem"]
            subprocess.call(["mysql", "-u{}".format(mysql_username), "-p{}".format(mysql_password), "-hlocalhost",
                             "alienvault_siem", "-e", "source mysql_setup.sql;"])
        except Exception as e:
            logging.error("Unexpected error happened while running setup sql. {}".format(type(e)))
            logging.debug(traceback_information(sys.exc_info()))
    shutil.copy("mysql_setup.sql.bak","mysql_setup.sql")
    return user_password


def main():


    # verification = getpass.getpass("Please enter the mysql password again: ")
    # # username = "root"
    # password = "yvdTPppbhy"
    # verification = "yvdTPppbhy"

    opts = args = None
    try:
        # Get config file arg (if exists)
        opts, args = getopt.getopt(sys.argv[1:], 'c:r', ["config=", "rollback", "only-rollback"])

    except getopt.GetoptError:
        sys.exit(1)

    conf = ""
    rb = 0
    for opt, arg in opts:
        if opt in ("-c", "--config", "--config="):
            conf = arg
        if opt in ("-r", "--rollback"):
            rb = 1
        if opt in ("--only-rollback"):
            rb = 2
    config,ossim_keys = read_config(conf)
    print(ossim_keys)
    for key in ossim_keys:
        try:
            if rb > 0:
                rollback(config, key, use_ssh, username, password, False)
            if rb < 2:
                print("Running setup for MySQL found at {}".format(config[key]["hostname"]))
                use_ssh = False if input("Is the mysql server on localhost? (y/n)").lower() == "y" else True
                username = input("Please enter the username of the mysql: ".format(config[key]["hostname"]))
                password = getpass.getpass("Please enter the mysql password: ")
                user_password = setup(config, key, use_ssh, username, password)
                config[key]["username"] = "ossim_logserver"
                print("The password of the generated user is:" + user_password)
                config[key]["password"] = user_password
                uid = str(uuid.uuid4())
                config[key]["id"] = uid
                config.write()
        except Exception as e:
            logging.error("Unexpected error happened while setting up Ossim configured under {}. {}".format(key,type(e)))
            logging.debug(traceback_information(sys.exc_info()))
    sys.exit(0)


if __name__ == '__main__':
    main()
