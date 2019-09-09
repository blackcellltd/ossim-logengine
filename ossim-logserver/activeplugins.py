import logging
import os
import subprocess
import sys

import ossim_logserver
from pymongo import MongoClient, errors

# TODO: file name based on 'Ossim Key'
def max_line_counter(file_rt):
    num = subprocess.Popen("cat {} | wc -l".format(file_rt), shell=True, stdout=subprocess.PIPE)
    num = str(num.communicate())
    a = 3
    b = num.rfind('\\')
    return int(num[a:b])


config_file = '/etc/ossim/logserver.conf'
plugin_logger = logging.getLogger("ossim_logger.activePlugins")

config, ossim_keys = ossim_logserver.read_config(config_file, plugin_logger)
plugin_logger.info("Initializing active plugin/sid query.")
try:
    # Connect to the database specified in the config file
    client = MongoClient("{}:{}".format(config["mongo"]["hostname"], config["mongo"]["port"]))
    db = client.get_database(config["mongo"]["database"])
    db.authenticate("justread", config["mongo"]["justread"])

    plugin_logger.info("Connection to database successful. Checking if files already exist...")

    # Open the file that contains the list of active plugins
    if os.path.isfile("/usr/share/python/ossim-logserver/activePlugins.list"):
        act_plugins = open("/usr/share/python/ossim-logserver/activePlugins.list", 'r')
        fresh_plugins_file = False
        plugin_logger.info("activePlugins.list found.")
    else:
        act_plugins = open("/usr/share/python/ossim-logserver/activePlugins.list", 'w')
        act_plugins.close()
        act_plugins = open("/usr/share/python/ossim-logserver/activePlugins.list", 'a')
        fresh_plugins_file = True
        plugin_logger.info("activePlugins.list not found, creating file.")

    # Open the file that contains the list of active sids
    if os.path.isfile("/usr/share/python/ossim-logserver/activeSids.list"):
        act_sids = open("/usr/share/python/ossim-logserver/activeSids.list", 'r')
        fresh_sids_file = False
        plugin_logger.info("activeSids.list found.")
    else:
        act_sids = open("/usr/share/python/ossim-logserver/activeSids.list", 'w')
        act_sids.close()
        act_sids = open("/usr/share/python/ossim-logserver/activeSids.list", 'a')
        fresh_sids_file = True
        plugin_logger.info("activeSids.list not found, creating file.")

    # Do the initial query
    try:
        for key in ossim_keys:
            plugins = db.log.aggregate([{'$match': {'ossim_id': config[key]['id']}},
                                        {"$group": {"_id": {"plugin_id": "$plugin_id"}}}])

            sids = db.log.aggregate([{'$match': {'ossim_id': config[key]['id']}},
                                     {"$group": {"_id": {"plugin_id": "$plugin_id", "plugin_sid": "$plugin_sid"}}}])

            plugin_logger.info("Database query successful.")

            # If the file is new, insert all plugin ids into it
            if fresh_plugins_file:
                activePlugins = []
                i = 0
                for line in plugins:
                    if i == 0:
                        # plugin_id = line["_id"]["plugin_id"]
                        activePlugins.append(line["_id"]["plugin_id"])
                        i += 1
                    else:
                        plugin_id = line["_id"]["plugin_id"]
                        j = 0
                        new_num = True
                        while j < i:
                            if plugin_id == activePlugins[j]:
                                new_num = False
                                break
                            j += 1
                        if new_num:
                            activePlugins.append(plugin_id)
                            i += 1

                # Place plugin ids in order
                plugin_num = i
                i = 0
                while i < plugin_num:
                    k = i + 1
                    while k < plugin_num:
                        if activePlugins[i] > activePlugins[k]:
                            c = activePlugins[i]
                            activePlugins[i] = activePlugins[k]
                            activePlugins[k] = c
                        k += 1
                    i += 1

                # Write ids to file
                i = 0
                while i < plugin_num:
                    act_plugins.write(str(activePlugins[i]) + '\n')
                    i += 1

                # Done.
                plugin_logger.info("Created a list of active plugins containing {} ids.".format(plugin_num))
                act_plugins.close()

            # If the file is present, only insert new entries
            else:
                max_lines = max_line_counter("/usr/share/python/ossim-logserver/activePlugins.list")
                i = 0
                activePlugins = []
                new_activePlugins = []
                new_ids = 0

                # Fill list up with known entries
                while i < max_lines:
                    activePlugins.append(int(act_plugins.readline()))
                    i += 1

                # Close file since we don't need it now
                act_plugins.close()

                # Put new entries into a list
                for line in plugins:
                    plugin_id = line["_id"]["plugin_id"]
                    i = 0
                    new_num = True
                    while i < max_lines:
                        if plugin_id == activePlugins[i]:
                            new_num = False
                        i += 1

                    # Append new number to list
                    if new_num:
                        new_activePlugins.append(plugin_id)
                        new_ids += 1

                # Place new plugin ids in order
                if new_ids > 0:
                    i = 0
                    while i < new_ids:
                        k = i + 1
                        while k < new_ids:
                            if new_activePlugins[i] > new_activePlugins[k]:
                                c = new_activePlugins[i]
                                new_activePlugins[i] = new_activePlugins[k]
                                new_activePlugins[k] = c
                            k += 1
                        i += 1

                    # Insert new plugin ids in the file
                    i = 0
                    act_plugins = open("/usr/share/python/ossim-logserver/activePlugins.list", 'a')
                    while i < new_ids:
                        act_plugins.write(str(new_activePlugins[i]) + '\n')
                        i += 1
                    plugin_logger.info("Inserted {} ids. The list now contains {} ids.".format(new_ids,
                                                                                               new_ids+max_lines))
                    act_plugins.close()
                else:
                    plugin_logger.info("No new ids were found.")

                # Done.

            # If the file is new, insert all plugin sids into it
            if fresh_sids_file:
                activeSids = []
                i = 0
                for line in sids:
                    if i == 0:
                        plugin_id = line["_id"]["plugin_id"], line["_id"]["plugin_sid"]
                        activeSids.append(plugin_id)
                        i += 1
                    else:
                        plugin_id_sid = line["_id"]["plugin_id"], line["_id"]["plugin_sid"]
                        j = 0
                        new_sid = True
                        while j < i:
                            if plugin_id_sid == activeSids[j]:
                                new_sid = False
                                break
                            j += 1

                        if new_sid:
                            activeSids.append(plugin_id_sid)
                            i += 1

                # TODO: Placing SIDS in order

                # Write sids to file
                sid_num = i
                i = 0
                while i < sid_num:
                    act_sids.write(str(activeSids[i]) + '\n')
                    i += 1

                # Done.
                plugin_logger.info("Created a list of active SIDs containing {} SIDs.".format(sid_num))
                act_sids.close()

            # If the file exists, only insert the new SIDs
            else:
                max_lines = max_line_counter("/usr/share/python/ossim-logserver/activeSids.list")
                i = 0
                reform_sids = []
                activeSids = []
                new_activeSids = []
                new_sids = 0

                # Fill list up with known entries
                while i < max_lines:
                    reform_sids.append(act_sids.readline())
                    i += 1

                # Close file since we don't need it now
                act_sids.close()

                # Reformat sids to have them as integers
                i = 0
                while i < max_lines:
                    a_first = reform_sids[i].find('(') + 1
                    b_first = reform_sids[i].find(',')
                    a_second = reform_sids[i].find(' ') + 1
                    b_second = reform_sids[i].rfind(')')
                    activeSids.append((int(reform_sids[i][a_first:b_first]), int(reform_sids[i][a_second:b_second])))
                    i += 1

                # Put new entries into a list
                for line in sids:
                    plugin_id_sid = line["_id"]["plugin_id"], line["_id"]["plugin_sid"]
                    i = 0
                    new_sid = True
                    while i < max_lines:
                        if plugin_id_sid == activeSids[i]:
                            new_sid = False
                            break
                        i += 1
                    if new_sid:
                        new_activeSids.append(plugin_id_sid)
                        new_sids += 1

                if new_sids > 0:

                    # TODO: Place sids in order

                    # Insert new sids into file
                    i = 0
                    act_sids = open("/usr/share/python/ossim-logserver/activeSids.list", 'a')
                    while i < new_sids:
                        act_sids.write(str(new_activeSids[i]) + '\n')
                        i += 1
                    plugin_logger.info("Inserted {} sids. The list now contains {} sids.".format(new_sids,
                                                                                                 new_sids+max_lines))
                    act_sids.close()
                else:
                    plugin_logger.info("No new sids were found.")

                # Done.

    # If query fails, raise error
    except errors.OperationFailure:
        plugin_logger.error("Database query failed: {}".format(pymongo.error.OperationFailure.details))
        sys.exit(1)

# If connection fails, raise error
except errors.ConnectionFailure:
    plugin_logger.error("Connection to {} on port {} failed.".format(config["mongo"]["hostname"],
                                                                     config["mongo"]["port"]))
    sys.exit(1)
