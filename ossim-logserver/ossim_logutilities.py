"""
Utility file, containing methods used in multiple other modules
"""
import logging
import os
from contextlib import contextmanager
import configobj
import sys
import socket, struct
from binascii import hexlify


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


def setup_logger(config, logger):
    """
    Set up the logger received as an argument. Utility function used for code redundancy reduction.

    :param config: Dictionary, containing at least the keys "logfile" and "loglevel".
    :param logger: Logger object, output of logging.getLogger().
    :return : Does not return anything.
    """
    logfile = config.get("logfile")

    loglevel = config.get("loglevel") if config.get("loglevel", None) is not None else logging.DEBUG

    if logfile is not None:
        fh = logging.FileHandler(logfile)
    else:
        fh = logging.StreamHandler()

    fh.setLevel(loglevel)
    logger.setLevel(loglevel)
    fh.setFormatter(logging.Formatter('[%(asctime)s]:%(name)s:%(levelname)s: %(message)s'))
    logger.addHandler(fh)


def get_uuid_string_from_bytes(uuid_bytes):
    """Returns the uuid canonical string from a set of bytes"""
    import uuid
    if uuid_bytes is not None:
        return str(uuid.UUID(bytes=uuid_bytes))
    else:
        return ""


def get_bytes_from_uuid(uuid_str):
    """Returns the uuid bytes from a canonical uuid string"""
    import uuid
    id = uuid.UUID(uuid_str)
    return id.bytes


def get_ip_str_from_bytes(ip_bytes):
    """Return a str representation of an ip stored as bytes."""
    ip_str = ""
    try:
        ip_str = socket.inet_ntop(socket.AF_INET6, ip_bytes)
    except:
        ip_str = socket.inet_ntop(socket.AF_INET, ip_bytes)
    return ip_str


def get_ip_bin_from_str(ip_str):
    """Return a bytes representation of an ip stored as a string."""
    ip_bin = None
    if ip_str:
        try:
            ip_bin = socket.inet_pton(socket.AF_INET6, ip_str)
        except:
            ip_bin = socket.inet_pton(socket.AF_INET, ip_str)
    return ip_bin


def get_ip_hex_from_str(ip_str):
    """Return hex representation of an ip stored as a str."""
    ip_hex = None
    ip_bin = get_ip_bin_from_str(ip_str)
    if ip_bin:
        ip_hex = hexlify(ip_bin)
    return ip_hex


def get_mac_str_from_bytes(mac_bytes):
    """Returns the MAC address as a string from a binary MAC"""
    if mac_bytes is None:
        return ''
    else:
        return (':'.join([hexlify(mac_bytes).decode("utf8")[i:i + 2] for i in range(0, 12, 2)]))


def ip_str_to_int(ip, protocol=None):
    """
    Convert string IP representation to int..

    :param ip: IP address in string format.
    :return: IP address in int format
    """
    # packedIP = socket.inet_aton(ip)
    # return struct.unpack("!L", packedIP)[0]
    prot = socket.AF_INET
    if protocol is None:
        if is_valid_ipv6_address(ip):
            prot = socket.AF_INET6
    else:
        if protocol == 6:
            prot = socket.AF_INET6

    return int.from_bytes(socket.inet_pton(prot, ip), "big")


def ip_int_to_str(ip, protocol=4):
    """
    Convert int IP representation to string.

    :param ip: IP address in int format
    :return: IP address in string format
    """
    # packedIP = struct.pack('!L', ip)
    # return socket.inet_ntoa(packedIP)

    prot = socket.AF_INET
    length = 4
    if protocol == 6:
        prot = socket.AF_INET6
        length = 16
    return socket.inet_ntop(prot, (ip).to_bytes(length, "big"))


def is_valid_ipv6_address(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:  # not a valid address
        return False
    return True


def convert_mongo_records_to_json(records, in_logger=None):
    import json
    from bson import ObjectId
    import datetime
    if in_logger is None:
        in_logger = logging.getLogger("ossim_logger.archiver")

    IP_KEYS = ["ip_src", "ip_dst", "dst_host", "dst_net", "src_host", "src_net"]
    try:
        for i in range(len(records)):
            current_dict = records[i]
            edited = False
            for key in current_dict:
                if key == "timestamp" and isinstance(current_dict[key], datetime.datetime):
                    current_dict[key] = current_dict[key].strftime("%Y-%m-%d %H:%M:%S.%f")
                    edited = True
                if key == "_id" and isinstance(current_dict[key], ObjectId):
                    current_dict[key] = str(current_dict[key])
                    edited = True
                if key in IP_KEYS and isinstance(current_dict[key], bytes):
                    current_dict[key] = get_ip_str_from_bytes(current_dict[key])
                    edited = True
            if edited == True:
                records[i] = current_dict

        return records
    except Exception as e:
        in_logger.error("Unexpected error happened while serializing mongo records to json: {}".format(type(e)))
        in_logger.debug(traceback_information(sys.exc_info()))

        return []


def convert_json_to_mongo_records(json_string, in_logger=None):
    import json
    from bson import ObjectId
    import datetime
    if in_logger is None:
        in_logger = logging.getLogger("ossim_logger.archiver")

    IP_KEYS = ["ip_src", "ip_dst", "dst_host", "dst_net", "src_host", "src_net"]

    records = json.loads(json_string)
    try:
        for i in range(len(records)):
            current_dict = records[i]
            edited = False
            for key in current_dict:
                if key == "timestamp" and isinstance(current_dict[key], str):
                    current_dict[key] = datetime.datetime.strptime(current_dict[key], "%Y-%m-%d %H:%M:%S.%f")
                    edited = True
                elif key == "_id" and isinstance(current_dict[key], str):
                    current_dict[key] = ObjectId(current_dict[key])
                    edited = True
                elif key in IP_KEYS and isinstance(current_dict[key], str):
                    current_dict[key] = get_ip_bin_from_str(current_dict[key])
                    edited = True
            if edited == True:
                records[i] = current_dict
        return records
    except Exception as e:
        in_logger.error("Unexpected error happened while serializing mongo records to json: {}".format(type(e)))
        in_logger.debug(traceback_information(sys.exc_info()))

        return []


def _unpickle(filename):
    """ Wraps the pickle modules loading with file handling, for reduced code redundancy."""
    import pickle
    with open(filename, "rb") as f:
        return pickle.load(f)


def _pickle(obj, filename, protocol=None):
    """ Wraps the pickle modules dumping with file handling, for reduced code redundancy."""
    import pickle
    with open(filename, "wb") as f:
        return pickle.dump(obj, f, protocol=protocol if protocol is not None else pickle.DEFAULT_PROTOCOL)


def _files_maintenance(directory):
    try:
        files = _unpickle(os.path.join(directory, ".files"))
    except:
        files = {}
    try:
        done = _unpickle(os.path.join(directory, ".done"))
    except:
        done = []

    for uud in list(files):
        if uud in done:
            files.pop(uud)
            done.remove(uud)
    print(files, done)
    _pickle(files, os.path.join(directory, ".files"))
    _pickle(done, os.path.join(directory, ".done"))


@contextmanager
def get_database(hostname, port, database, username, password):
    import pymongo
    # hostname, port, database, username, password ="","","","",""

    # hostname = kwargs.get("hostname") if kwargs.get("hostname") is not None else config.get("parser").get("hostname")
    # port = kwargs.get("port") if kwargs.get("port") is not None else config.get("parser").get("port")
    # database = kwargs.get("database") if kwargs.get("database") is not None else config.get("parser").get("database")
    # username = kwargs.get("username") if kwargs.get("username") is not None else config.get("username")
    # password = kwargs.get("password") if kwargs.get("password") is not None else config.get("password")
    try:
        client = pymongo.MongoClient("{hostname}:{port}".format(hostname=hostname, port=port))
        db = client.get_database(database)
        if (username is not None) and (password is not None):
            db.authenticate(username, password)
        yield db
    except Exception as e:
        raise
    finally:
        client.close()


def get_line_count(filename):
    import mmap
    def mapcount(file):
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    with open(filename, "r+") as f:
        return mapcount(f)
