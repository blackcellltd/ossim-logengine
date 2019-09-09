#!/usr/bin/env python3
import pymongo
import sys
import getopt
import configobj
import logging

import sys
import subprocess
from Crypto import Random
from Crypto.Hash import SHA256
import getpass
import re


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


logging.basicConfig(filename="mongodb_install.log",
                    level="DEBUG",
                    format='[%(asctime)s] %(levelname)s: %(message)s')


def usage():
    """ Print usage of the script."""
    print("usage: mongodb_install.py [-c/--config configfile]")


def read_config(config_file):
    """
     Read config file given in config_file argument, parse its body.

     In order for this script to work, the config file must contain at least:
     - A section called mongo.
     - In the section, the following keywords:
        - database: Name of the database which will be used for mysql archiving.
        - hostname: Hostname where the MongoDB is accessible.
        - port: Port where the MongoDB is accessible.
        - collection: Name of the collection where the log records will be stored.

     For a detailed overview of the config file, see read_config in logserver.py.
     :param config_file: path to the config file
     """
    try:
        # TODO: ADDITONAL REFACTOR, move read cfg to utilities?
        optional = {}

        required = {
            "mongo": ["database", "hostname", "port", "collection"]
        }

        parser = configobj.ConfigObj(config_file)

        for key in required:
            if parser.get(key, None) is None:
                key_type = "Section" if isinstance(required.get(key), dict) else "Keyword"
                logging.error("{} {} not found!".format(key_type, key))
                sys.exit(2)
            elif isinstance(required.get(key), list):
                for subkey in required[key]:
                    if parser[key].get(subkey, None) is None:
                        logging.error("{} not found in section {}!".format(subkey, key))
                        sys.exit(2)

        for key in optional:
            if parser.get(key, None) is None:
                parser[key] = optional[key]
                logging.warning(
                    "The keyword {} was not found, defaulting to default value: {}".format(key, optional[key]))
            elif isinstance(optional.get(key), dict):
                for subkey in optional[key]:
                    if parser[key].get(subkey, None) is None:
                        parser[key][subkey] = optional[key][subkey]
                        logging.warning(
                            "The keyword {} was not found in section {}, defaulting to default value: {}".format(subkey,
                                                                                                                 key,
                                                                                                                 optional[
                                                                                                                     key][
                                                                                                                     subkey]))

        return parser

    except IOError:
        logging.error("Unable to read config file {configfile}!", configfile=parser.filename)
        sys.exit(2)
    except configobj.ParseError:
        logging.error("Error in config file {configfile} format!", configfile=parser.filename)


def create_indices(collection):
    """
    Create indexes specified in the documentation on the collection got in argument.

    :param collection:
    :return : None:
    """

    text_index = [
        pymongo.IndexModel([("data_payload", pymongo.TEXT), ("username", pymongo.TEXT), ("filename", pymongo.TEXT)] + [
            ("userdata" + str(i), pymongo.TEXT) for i in range(1, 10)], name="unified_textindex")]
    field_names = ["batch_name", "ctx", "device_id", "dst_host", "dst_hostname", "dst_mac", "dst_net", "id", "ip_dst",
                   "ip_proto", "ip_src", "layer4_dport", "layer4_sport",
                   "plugin_id", "plugin_sid", "src_host", "src_hostname",
                   "src_mac", "src_net", "timestamp"]

    index_models = []
    for name in field_names:
        keywords = {}
        # Hash is unique and required, so it is not partial or sparse
        if name == "id":
            keywords["unique"] = True
        else:
            # Check if the database version is bigger than 3.2, <3.2 does not support partial
            if collection.database.client.server_info()["versionArray"][0] > 3 or (
                            collection.database.client.server_info()["versionArray"][0] == 3 and
                            collection.database.client.server_info()["versionArray"][1] >= 2):
                keywords["partial"] = {name: {"$exists": True}}
            else:
                keywords["sparse"] = True

        index_models.append(pymongo.IndexModel([(name, pymongo.ASCENDING)], **keywords))

    collection.create_indexes(index_models + text_index)


def create_archived_collection(db):
    coll = db.get_collection("archived")
    field_names = ["ossim_id", "batch_name", "batch_timestamp", "archive_timestamp"]
    index_models = []
    for name in field_names:
        index_models.append(pymongo.IndexModel([(name, pymongo.ASCENDING)]))
    coll.create_indexes(index_models)


def default_roles(db, collection):
    """ Return a list of default roles, used in the creation of the default users. """
    roles = []
    # User for the server to insert log records into the db
    justinsert = {
        "rolename": "justinsert",
        "privileges": [
            {"resource": {
                "db": db.name,
                "collection": collection.name},
                "actions": ["insert"]},
            {"resource": {
                "db": db.name,
                "collection": "archived"},
                "actions": ["insert"]}
        ],
        "roles": []
    }
    # User for querying log records ONLY from the log collection
    justread = {
        "rolename": "justread",
        "privileges": [
            {"resource": {
                "db": db.name,
                "collection": collection.name},
                "actions": ["find"]},
            {"resource": {
                "db": db.name,
                "collection": "archived"},
                "actions": ["find"]}
        ],
        "roles": []
    }

    roles.append(justinsert)
    roles.append(justread)
    return roles


def default_users():
    """ Return a list of default users, used by the other scripts. """
    users = []
    userdata = [{"username": "justinsert",
                 "password": SHA256.new(Random.new().read(50)).hexdigest(),
                 "customData": {"note": "User only for log insertion"},
                 "roles": ["justinsert"],
                 "digestPassword": True},
                {"username": "justread",
                 "password": SHA256.new(Random.new().read(50)).hexdigest(),
                 "customData": {"note": "User only for querying"},
                 "roles": ["justread"],
                 "digestPassword": True
                 }]
    users.extend(userdata)
    return users


def create_roles(db, roles):
    """ Create roles gives as parameter roles.

    Help for the privileges and roles format:
   {"rolename": "",
        "privileges": [
            {"resource": {
                "db": db.name,
                "collection": collection.name},
                "actions": [""]}],
        "roles": []
    }

    :param db: Database where the roles will be created, must be authenticated if necessary.
    :param users: List of dicts, containing  'rolename','privileges','roles' keys.
    :return : None
    """
    if isinstance(roles, list) and isinstance(db, pymongo.database.Database):
        for role in roles:
            if isinstance(role, dict):
                db.command("createRole", role["rolename"], privileges=role["privileges"], roles=role["roles"])


def create_admin(cli):
    """ Get input form the user, and create an all powerful superuser.

    :param cli: PymongoClient object.
    """
    root = {"username": input('Please type in the database owner username: '),
            "password": getpass.getpass(prompt='Please type in the database owner password: '),
            "customData": {"note": "Database owner"},
            "roles": ["root"],
            "digestPassword": True
            }
    cli.admin.command("createUser", root["username"], pwd=root["password"], roles=root["roles"],
                      digestPassword=root["digestPassword"])


def create_users(db, users):
    """ Create all users given as a list through the argument users.

    Format for each user found in users:
    {"username": "",
     "password": "",
     "customData": {"note": ""},
     "roles": [],
     "digestPassword": True}

    :param db: Database where the users will be created
    :param users: List of dicts, containing  'username','password','roles', 'customData' keys
    :return : None
    """

    if isinstance(db, pymongo.database.Database) and isinstance(users, list):
        # TODO: replace password with anything
        for user in users:
            db.command("createUser", user["username"], pwd=user["password"], roles=user["roles"], digestPassword=True)


def rollback(db, collection, admin_name, was_error=True):
    """ Rollback changes on MongoDB made by this script.

    Removes all indexes from collection, drops all roles and users made by default users and default roles.
    If an admin_name is given, it only removes that user from the admin users, if None is given, it removes all admin users.

    :param db: Database object, where the users shall be created.
    :param collection: Collection object, where the users will have privileges.
    :param admin_name: Name of the admin user to be removed.
    """
    if was_error:
        cont = input("An error occured during the setup script, please see the logs. Do you want to rollback? (y/n) ")
        cont = True if cont.lower() == "y" else False
    else:
        cont = True
    if cont:
        collection.drop_indexes()
        roles = [role["rolename"] for role in default_roles(db, collection)]
        for role in roles:
            try:
                db.command("dropRole", role)
            except:
                print("Rollback, no role {}".format(role))

        users = [user["username"] for user in default_users()]
        for user in users:
            try:
                db.remove_user(user)
            except:
                print("Rollback, no user {}".format(user))

        try:
            if admin_name is not None:
                db.client.admin.remove_user(admin_name)
            else:
                for user in db.client.admin.command("usersInfo")["users"]:
                    db.client.admin.remove_user(user["user"])
        except:
            print("Rollback, no admin user found with name {}".format(admin_name))


def deauth_mongod_config():
    """ Modify the mongodb config file at /etc/mongod.conf and disable authorization, """
    lines = []
    restart = False
    with open("/etc/mongod.conf", "r") as f:
        lines = f.readlines()
    with open("/etc/mongod.conf", "w") as f:
        for line in lines:
            match = re.search(".*authorization\s?:\s?enabled.*", line)
            if match is None:
                f.write(line)
            else:
                f.write("  authorization: disabled\n")
                restart = True
    return restart


def enable_mongod_auth():
    """ Modify the mongodb config file at /etc/mongod.conf, and add the line authorization: enabled under the security section  """
    lines = []
    no_sec, line_no = -1, 0
    with open("/etc/mongod.conf", "r") as f:
        lines = f.readlines()
    # Search for a security: tag
    for line in lines:
        if re.search("([^#]|^)security:.*", line) is not None:
            no_sec = line_no
        line_no += 1
    # If there is no security tag, just add it to the end
    if no_sec < 0:
        with open("/etc/mongod.conf", "a") as f:
            f.write("security:\n")
            f.write("  authorization: enabled\n")
    else:
        hit = False
        # There is a security tag,
        for line in lines:
            match_dis = re.search(".*authorization\s?:\s?disabled.*", line)
            match_en = re.search(".*authorization\s?:\s?enabled.*", line)
            # Search for authorization: disabled, and change it
            if match_dis is not None:
                lines[lines.index(line)] = "  authorization: enabled\n"
                hit = True
                break
            # Search for authorization: enabled, if there is, don't do anything
            # Note though that this case should never happen.
            if match_en is not None:
                hit = True
                break

        if hit is False:
            lines.insert(line_no + 1, "  authorization: enabled\n")
        with open("/etc/mongod.conf", "w") as f:
            f.writelines(lines)
    subprocess.call(["/etc/init.d/mongod", "restart"])
    print("Mongodb successfully restarted.")


def main():
    """Get command line arguments, read the config file, and start index creation."""
    # Acquire config data
    opts = args = None
    try:
        # Get config file arg (if exists) and rollback args
        opts, args = getopt.getopt(sys.argv[1:], 'c:r', ["config=", "rollback", "only-rollback"])

    except getopt.GetoptError:
        usage()
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
    config = read_config(conf)

    # enable_mongod_auth()
    deauth_mongod_config()
    subprocess.call(["/etc/init.d/mongod", "restart"])

    # Initialize DB connection
    try:
        client = pymongo.MongoClient(config["mongo"]["hostname"] + ":" + str(config["mongo"]["port"]))
        db = client.get_database(config["mongo"]["database"])
        collection = db.get_collection(config["mongo"]["collection"])
    except Exception as e:
        logging.error("Could not connect to database, or could not retrieve database/collection.")
        logging.debug(traceback_information(e_info=sys.exc_info()))
        sys.exit(1)

    if rb > 0:
        rollback(db, collection, None, False)
    if rb == 2:
        sys.exit(0)

    users = []
    admin_name = None
    # Setup db
    try:
        create_indices(collection)
        create_archived_collection(db)
        create_roles(db, default_roles(db, collection))
        users = default_users()
        create_users(db, users)
        admin_name = create_admin(client)
    except Exception as e:
        logging.error("Could not create default indexes, roles and users,rolling back changes!")
        logging.debug(traceback_information(e_info=sys.exc_info()))
        rollback(db, collection, admin_name)
        sys.exit(1)
    # Write new configuration data
    try:
        for user in users:
            config["mongo"][user["username"]] = user["password"]
        config.write()
        print("Mongo setup ended.")
    except:
        logging.error("Could not write new config file!")
        logging.debug(traceback_information(e_info=sys.exc_info()))
        rollback(db, collection, admin_name)
        sys.exit(1)

    try:
        enable_mongod_auth()
    except:
        logging.error("Could not write MongoDB config file!")
        # rollback(db, collection, admin_name)


if __name__ == '__main__':
    main()
