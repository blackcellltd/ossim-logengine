import datetime
import gzip
import logging
import os
import socket
from binascii import hexlify, unhexlify
import sshtunnel
from pymongo.errors import BulkWriteError
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.sql
import sys
from sqlalchemy import text as sql_text
import sqlalchemy.schema
import uuid
from ossim_logutilities import get_database, setup_logger, traceback_information, get_uuid_string_from_bytes, \
    get_bytes_from_uuid, get_ip_str_from_bytes, get_ip_bin_from_str, get_ip_hex_from_str, get_mac_str_from_bytes, \
    convert_mongo_records_to_json, convert_json_to_mongo_records
from timestamp_query import get_timestamps, generate_ts_query
import time
archiver_logger = logging.getLogger("ossim_logger.archiver")

UUIDS = ["id", "ctx"]
IPS = ["src_host", "ip_dst", "src_net", "dst_host", "dst_net", "ip_src"]
MACS = ["src_mac", "dst_mac"]


def query_new_records(config, ossim_key, sql_lock):
    """ Query the mysql server found with config, insert the records into the mongodb, and also archive them.

    If another process is running with the same sql_lock acquired, this process will terminate after 20 seconds.

    :param config: Dictionary containing cionfiguration values. See read_config in ossim_logserver.py.
    :param sql_lock: multiprocessing.Lock object, used to sync the query and the archive file moving.
    """
    setup_logger(config, archiver_logger)
    archiver_logger.debug("Query process starting ({}), requesting lock".format(str(os.getpid())))
    try:
        if sql_lock.acquire(True, int(config[ossim_key]["mysql_callback_time"]) / 3):
            try:
                archive_directory = os.path.join(config["archive_directory"], config[ossim_key]["id"])
                os.makedirs(archive_directory, exist_ok=True)
                archiver_logger.debug("Lock granted to query.({})".format(str(os.getpid())))
                using_tunnel = False if config[ossim_key]["tunnel_pwd"] == "" else True

                # Set up ssh tunnel if needed, formalize login data
                if using_tunnel:
                    login_data = {
                        "user": config[ossim_key]["username"],
                        "pw": config[ossim_key]["password"],
                        "port": "8081",
                        "hostname": "127.0.0.1",
                        "db": "alienvault_siem"
                    }
                    tunnel = sshtunnel.SSHTunnelForwarder(
                        (config[ossim_key]["hostname"], int(config[ossim_key]["port"])),
                        ssh_username="tunnel",
                        ssh_password=config[ossim_key]["tunnel_pwd"],
                        remote_bind_address=('127.0.0.1', 3306)  # ,
                        # local_bind_address=('127.0.0.1', 8081)
                    )
                    tunnel.start()
                    login_data["port"] = tunnel.local_bind_port
                else:
                    login_data = {
                        "user": config[ossim_key]["username"],
                        "pw": config[ossim_key]["password"],
                        "port": config[ossim_key]["port"],
                        "hostname": config[ossim_key]["hostname"],
                        "db": "alienvault_siem"
                    }

                result_count = 0
                engine = sqlalchemy.create_engine(
                    'mysql+pymysql://{user}:{pw}@{hostname}:{port}/{db}'.format(**login_data))
                # Get the new id count. If there are none, exit.
                with engine.connect() as con:
                    rs = con.execute("SELECT count(id) FROM logarchive.new_ids ;")
                    result_count = rs.fetchone()
                    result_count = result_count[0] if result_count is not None else 0
                    if result_count <= 0:
                        archiver_logger.info("There are {} new ids found, nothing to do.".format(result_count))
                        return
                    con.execute(
                        "DELETE FROM logarchive.new_ids WHERE new_ids.id NOT IN (SELECT id FROM alienvault_siem.acid_event);")
                # TODO: NORMAL NUMBER FOR DIVISOR
                for i in range(int(result_count / 100000) + 1):
                    batch_name = ""
                    # Get whether there is already an archive file
                    for item in os.listdir(archive_directory):
                        split = os.path.splitext(item)
                        if split[1] == ".ar":
                            batch_name = split[0]
                    # If there is not, then create one
                    if batch_name == "":
                        batch_name = os.path.join(archive_directory,
                                                  datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".ar")
                        f = open(batch_name, "w")
                        f.close()

                    records = []
                    ids = []
                    with engine.connect() as con:
                        select = sql_text("""SELECT acid_event.*,extra_data.* FROM logarchive.new_ids
            JOIN alienvault_siem.acid_event ON alienvault_siem.acid_event.id = logarchive.new_ids.id
            JOIN alienvault_siem.extra_data ON alienvault_siem.acid_event.id = alienvault_siem.extra_data.event_id LIMIT 100000;""")

                        rs = con.execute(select)
                    for rec in rs:
                        data = {}
                        for key in rs.keys():
                            value = rec[key]
                            if key == "event_id":
                                continue
                            if key == "id":
                                ids.append(value)
                            if isinstance(value, bytes):
                                if key in UUIDS:
                                    # the record is presumed to be a uuid
                                    data[key] = get_uuid_string_from_bytes(value)
                                elif key in IPS:
                                    # the value is presumed to be an ip
                                    data[key] = value
                                elif key in MACS:
                                    # the value is presumed to be a mac
                                    data[key] = get_mac_str_from_bytes(value)
                                    # if len(value) == 16:
                                    #     # the record is presumed to be a uuid
                                    #     data[key] = get_uuid_string_from_bytes(value)
                                    # elif len(value) == 4:
                                    #     # the value is presumed to be an ip
                                    #     data[key] = int.from_bytes(
                                    #         get_ip_bin_from_str(get_ip_str_from_bytes(value)), byteorder="big")
                                    # elif len(value) == 6:
                                    #     # the value is presumed to be a mac
                                    #     data[key] = get_mac_str_from_bytes(value)
                            else:
                                data[key] = value
                        data["batch_name"] = os.path.splitext(batch_name)[0]
                        data["ossim_name"] = config[ossim_key]["name"]
                        data["ossim_id"] = config[ossim_key]["id"]
                        records.append(data)

                    len_of_records = len(records)
                    if len_of_records != 0:
                        not_duplicate_ids = insert_records_into_db(records, config)

                        # Store the true length, becasue archive_to_file modifies the contents of the list.
                        full = archive_to_file(records, archive_directory)
                        if full:
                            archive_file(config, ossim_key, sql_lock)
                        for id in not_duplicate_ids:
                            ids.remove(get_bytes_from_uuid(id))

                        delete = sql_text("""DELETE FROM logarchive.new_ids WHERE id IN :ids;""")
                        with engine.connect() as con:
                            con.execute(delete, ids=ids)
                    archiver_logger.info("Copied {} records into mongodb.".format(len_of_records))
            except Exception as e:
                archiver_logger.error("Unexpected error happened while archiving mysql records {}.".format(type(e)))
                archiver_logger.debug(traceback_information(sys.exc_info()))
            finally:
                sql_lock.release()
                archiver_logger.debug("Released lock from query.({})".format(str(os.getpid())))
                if using_tunnel:
                    tunnel.stop()
        else:
            archiver_logger.debug("Did not receive lock, exiting process.({})".format(str(os.getpid())))
            sys.exit(0)
    except Exception as e:
        archiver_logger.error("Unexpected error happened while acquiring lock for mysql archiving {}.".format(type(e)))
        archiver_logger.debug(traceback_information(sys.exc_info()))


def archive_to_file(records, folder):
    """ Archive records to the .ar file in folder.

    Searches folder for a .ar file, reads the records, then converts all records to json serializeable format.
    Gzips the records, and writes the updatd records back to the .ar file. If the line number is greater than 99999,
    returns true, marking that the file is full.

    :param records: List of records suitable for mongodb insertion.
    :param folder: Path to the folder where the archives should be saved.
    """
    try:
        import json
        from bson.objectid import ObjectId
        import datetime

        for item in os.listdir(folder):
            split = os.path.splitext(item)
            if split[1] == ".ar":
                records.extend(read_from_archive(os.path.join(folder, item)))
                filename = split[0]

        transformed_records = convert_mongo_records_to_json(records.copy(), archiver_logger)

        with gzip.open(os.path.join(folder, filename + ".ar"), "wb") as f:
            d = json.dumps(transformed_records, f).encode("utf8")
            f.write(d)

        return len(transformed_records) > 99999
    except:
        archiver_logger.error(traceback_information(sys.exc_info()))


def read_from_archive(filename):
    """ Read the records found in path filename, and convert them to MongoDB format.

    If the file does not exist, or there wasn't anything found in the file, returns an empty list.

    :param filename: Path to the file to be read.
    :return : List of records, extracted form the file.
    """
    import json
    from bson.objectid import ObjectId
    import datetime
    data = ""
    if os.path.isfile(filename):
        with open(filename, "rb") as f:
            data = f.read()
        if len(data) < 1:
            return []
    else:
        return []
    data_str = gzip.decompress(data).decode("utf8")
    return convert_json_to_mongo_records(data_str, archiver_logger)
    # records = json.loads(data.decode("utf8"))
    #
    # for i in range(len(records)):
    #     current_dict = records[i]
    #     edited = False
    #     for key in current_dict:
    #         if key == "timestamp":
    #             current_dict[key] = datetime.datetime.strptime(current_dict[key], "%Y-%m-%d %H:%M:%S.%f")
    #             edited = True
    #         elif key == "_id":
    #             current_dict[key] = ObjectId(current_dict[key])
    #             edited = True
    #     if edited == True:
    #         records[i] = current_dict
    # return records


def archive_file(config, ossim_key, sql_lock, filename=None):
    """ Generate timestamps and archive the .ar file found in folder (or given with folder+filename).

    Takes the file either given with folder+filename, or the .ar file found in folder.
    Acquire sql_lock, rename the .ar file to .gz, generate timestamps for it, and move them to their folder.

    :param folder: Path to the archive folder.
    :param sql_lock: multiprocessing.Lock object, used for synchronizing with query_new_records.
    :param filename: Name of the archive file. If None, tries finding .ar file in folder.
    """
    from re import match
    from shutil import move
    # Acquire lock
    folder = os.path.join(config['archive_directory'], config[ossim_key]["id"])
    setup_logger(config, archiver_logger)

    def _inner(filename):
        if filename is None:
            if os.path.isdir(folder):
                for item in os.listdir(folder):
                    if os.path.splitext(item)[1] == ".ar":
                        filename = os.path.join(folder, item)
        else:
            filename = os.path.join(folder, filename)
        move(filename, os.path.splitext(filename)[0] + ".gz")

        filename = os.path.splitext(filename)[0] + ".gz"
        archiver_logger.info("Created archive file {}, requesting timestamps.".format(filename))
        # Generate hash, get timestamps for the hash
        query = generate_ts_query(filename)
        get_timestamps(filename, query, archiver_logger)
        base_filename = os.path.splitext(filename)[0]
        os.mkdir(base_filename)
        # Copy all relevant files to their folder
        for item in os.listdir(folder):
            if match("({}).*".format(os.path.basename(base_filename)), item) is not None:
                if (os.path.isfile(os.path.join(folder, item))):
                    move(os.path.join(folder, item),
                         os.path.join(folder, os.path.basename(base_filename), item))
        try:
            batch_name = os.path.splitext(filename)[0]
            timestamp = time.time()
            archiver_logger.debug("Addig archived file {} to mongodb archived scheme.".format(filename))
            with get_database(config["mongo"]["hostname"], config["mongo"]["port"], config["mongo"]["database"],
                              "justinsert",
                              config["mongo"]["justinsert"]) as db:
                db.get_collection("archived").insert_one(
                    {"ossim_id": config[ossim_key]["id"], "batch_name": batch_name,
                     "batch_timestamp": datetime.datetime.strptime(os.path.split(batch_name)[1],"%Y_%m_%d_%H_%M_%S").timestamp(),
                     "archive_timestamp": timestamp})  # Version where inconsistency appears between archived and mongo
            archiver_logger.debug("Successfully added archived file {} to mongodb.".format(filename))
        except Exception as e:
            archiver_logger.error("Could not add archived file to mongo {}. ".format(filename))
            archiver_logger.debug(traceback_information(sys.exc_info()))

            # batch_name = os.path.splitext(filename)[0]
            # with get_database(config["mongo"]["hostname"], config["mongo"]["port"], config["mongo"]["database"],
            #                   "justinsert",
            #                   config["mongo"]["justinsert"]) as db:
            #     db.get_collection(config["mongo"]["collection"]).update_many({"batch_name":batch_name,},{"$set":{"archived":True}})

    try:
        if sql_lock.acquire(True, 20):
            archiver_logger.debug("Acquired lock for file achiving.({})".format(str(os.getpid())))
            try:
                _inner(filename)
            except:
                archiver_logger.error("Could not archive file {}. ".format(filename))
                archiver_logger.debug(traceback_information(sys.exc_info()))
            finally:
                sql_lock.release()
        else:
            archiver_logger.warning("Could not acquire lock for file archiving.({})".format(str(os.getpid())))
            sys.exit(0)
    except:
        archiver_logger.error(traceback_information(sys.exc_info()))


def insert_records_into_db(records, config):
    """ Insert records into mongodb, with the parameters found in config.

    :param records: List of records in mongo compatible format, to be inserted.
    :param config: Configuration dictionary containing info about the mongoDB. See read_config in ossim_logserver.py
    :return : List of ids that were not inserted into the database due to an error, and should not be removed from the mysql table.
    """
    if len(records) == 0:
        return []
    try:
        with get_database(config["mongo"]["hostname"], config["mongo"]["port"], config["mongo"]["database"],
                          "justinsert",
                          config["mongo"]["justinsert"]) as db:
            db.get_collection(config["mongo"]["collection"]).insert_many(records, ordered=False)
        return []
    except BulkWriteError as bwe:
        not_duplicate_error = False
        not_duplicate_ids = []

        for error_dict in bwe.details["writeErrors"]:
            if int(error_dict["code"]) != 11000:
                not_duplicate_ids.append(error_dict["errmsg"].split('"')[1])
                not_duplicate_error = True
        if not_duplicate_error:
            archiver_logger.error("Bulk Write error happened while inserting into mongodb.")
            archiver_logger.debug(
                "Sample of the bulk write error: {}: {} {}".format(bwe.details["writeErrors"][0]["code"],
                                                                   bwe.details["writeErrors"][0]["errmsg"]))
        return not_duplicate_ids


def main():
    pass


if __name__ == "__main__":
    main()
