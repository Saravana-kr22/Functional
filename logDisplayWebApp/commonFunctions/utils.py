#
#
#  Copyright (c) 2023 Project CHIP Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import asyncio
import datetime
import io
import json
import logging
import os
import select
import shlex
import shutil
import subprocess
import sys
import traceback
import datetime as dt

import yaml
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse

script_executions_stats = {}
html_error = """
            <html>
            <head>
                <title>Log Display Web App</title>
            </head>
            <body>
                <h1>error_message</h1>
            </body>
        </html>
            """

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def config_reader():
    try:
        args = sys.argv
        if len(args) != 0 and "--config" not in args:
            config_yaml_file = os.path.join(os.getcwd(), "config", "config.yaml")
            if not os.path.exists(config_yaml_file):
                logging.error("The config file does not exist! exiting now! ",exc_info=True)
                sys.exit(0)
            with io.open(config_yaml_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        elif "--config" in args:
            config_yaml_file = args[1]
            if not os.path.exists(config_yaml_file):
                logging.error("The config file does not exist! exiting now! ",exc_info=True)
                sys.exit(0)
            with io.open(config_yaml_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
    except Exception as e:
        logging.error(e,exc_info=True)


def get_directory_info(dirs_list: list, log_dir: str) -> list:
    """
    this functions takes a list as argument and
    returns only the directory information of last modified,file size, file name, file location,
    in a list of dict objects
    {"dir_name": str,"dir_path":str,
    "dir_last_modified":unix_time, "dir_size":bytes }
    files are ignored and files that do not exist will be ignored
    """
    folder_details_list = []
    for dirs in dirs_list:
        try:
            full_path = os.path.join(log_dir, os.path.join(dirs))
            if not os.path.exists(full_path) or not os.path.isdir(full_path):
                logging.error("the path {} does not exist or is not a directory".format(full_path),exc_info=True)
                continue
            stat_obj = os.stat(full_path)
            dir_details = {"dir_name": dirs, "dir_path": full_path,
                           "dir_last_modified": dt.datetime.fromtimestamp(stat_obj.st_mtime).isoformat(),
                           "dir_size": stat_obj.st_size}
            folder_details_list.append(dir_details)
        except Exception as e:
            logging.error(e,exc_info=True)
            traceback.print_exc()
    folder_details_list = sorted(folder_details_list, key=lambda it: dt.datetime.fromisoformat(it["dir_last_modified"]))
    return folder_details_list


def zip_files(dir_path, dir_name):
    folder_path = os.path.join(dir_path, dir_name)
    if os.path.exists(folder_path):
        try:
            # Attempt to remove the directory and its contents
            logging.info("zipping the files")
            zip_file_path = os.path.join(dir_path, dir_name)
            shutil.make_archive(zip_file_path, 'zip', folder_path)
            logging.info("zipping the files has been completed")
            res = FileResponse(zip_file_path + ".zip", filename=dir_name + ".zip")
            return res
        except Exception as e:
            return {"success": False, "message": "error removing directory internal error"}
    else:
        return {"success": False, "message": "the path does not exist"}


def delete_files(dir_path, dir_name):
    full_path = os.path.join(dir_path, dir_name)
    if os.path.exists(full_path):
        try:
            # Attempt to remove the directory and its contents
            shutil.rmtree(full_path)
            return {"success": True, "message": f"The directory {dir_name} was successfully removed"}

        except Exception as e:
            logging.info(e)
            traceback.print_exc()
            return {"success": False, "message": "error removing directory internal error " + str(e)}
    else:
        return {"success": False, "message": "the path does not exist"}


def execute_bash_script(script_name, script_path, arguments, python_env):
    try:
        logger.info(f"Script '{script_name}' has Started execution ")
        global script_executions_stats
        command = f'{os.getcwd()}/bash_scripts/run_python_script.sh -python_environment {python_env} -script_name {script_name} -script_arguments "{arguments}" -python_script_path {script_path}'
        # Run the script and capture output
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        script_executions_stats.update({script_name: "Script has started execution"})
        timeout_seconds = 60
        while True:
            ready, _, _ = select.select([process.stdout], [], [], timeout_seconds)
            if process.stdout in ready:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if "completed pair and unpair sequence for" in output:
                        logger.info(output)
                        script_executions_stats.update({script_name: output})
            else:
                logger.error("Timeout reached")
                del script_executions_stats[script_name]
                process.kill()
                logger.info(f"Process Is Killed as it became unresponsive!!, can restart {script_name}")
                break

        # Get the return code
        return_code = process.returncode

        if return_code == 0:
            logger.info(f"Script {script_name} executed successfully.")
            del script_executions_stats[script_name]
        else:
            logger.error(f"Script {script_name} execution failed with return code {return_code}.")
            del script_executions_stats[script_name]
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def format_analytics_json_data(iteration_data_list: list) -> dict:
    analytics_dict = {}
    for iteration_data in iteration_data_list:
        analytics_data = iteration_data.get("iteration_data").get("iteration_tc_analytics_data")
        analytics_keys = analytics_data.keys()
        for analytics_key in analytics_keys:
            if analytics_key in analytics_dict:
                if iteration_data.get("iteration_data").get("iteration_tc_analytics_data").get(analytics_key) == {}:
                    continue
                else:
                    analytics_dict[analytics_key].update(
                        {str(iteration_data.get("iteration_number")):
                            iteration_data.get("iteration_data").get("iteration_tc_analytics_data").get(analytics_key)})
            else:
                if iteration_data.get("iteration_data").get("iteration_tc_analytics_data").get(analytics_key) == {}:
                    continue
                else:
                    analytics_dict.update({analytics_key: {
                        str(iteration_data.get("iteration_number")):
                            iteration_data.get("iteration_data").get("iteration_tc_analytics_data").get(analytics_key)
                      }
                    })
    return {"analytics": analytics_dict}


def analytics_json_get(path):
    """
    returns the data in form of
    {
      "analytics": {
        "some_analytics": {
          "1": 1.3177,
          "2": 1.3864,
          "3": 1.4032
        },
        "heap_usage": {
          "1": 1299.408,
          "2": 1299.408,
          "3": 1299.408
        }
      }
    }
    """
    try:
        full_path = os.path.join(path, "summary.json")
        fp = open(full_path, "r")
        json_data = json.load(fp)
        fp.close()
        analytics_data = format_analytics_json_data(json_data.get("list_of_iteration_records"))
        return analytics_data
    except Exception as e:
        logging.error(e,exc_info=True)
        return "no data"


def summary_json_find(path, filename):
    found_paths = []
    for root, dirs, files in os.walk(path):
        if filename in files:
            found_paths.append(os.path.join(root, filename))
    return found_paths


def validate_analytics_summary_json(full_paths):
    valid_paths = []
    for full_path in full_paths:
        try:
            with open(full_path, 'r') as fp:
                summary_json = json.load(fp)
                if "analytics_parameters" in summary_json["test_summary_record"]:
                    valid_paths.append(full_path)
        except Exception as e:
            logging.error(e, exc_info=True)
    return valid_paths


def remove_common_path(list_of_paths, log_dir):
    updated_path = []
    common_prefix = log_dir
    for path in list_of_paths:
        try:
            rel_path = os.path.relpath(path, common_prefix)
            updated_path.append(rel_path)
        except Exception as e:
            logging.error(e, exc_info=True)
    return updated_path, common_prefix


def add_path_to_tree(dir_path, tree, common_prefix):
    parts = dir_path.split("/")
    current_node = tree
    for part in parts:
        if part == "summary.json":
            fp = open(os.path.join(common_prefix, dir_path))
            data = json.load(fp)
            fp.close()
            analytics = data["test_summary_record"]["analytics_parameters"]
            for analytic in analytics:
                new_node = {
                    "id": f"{current_node.get('id')}**{analytic}",
                    "text": analytic.upper()
                }
                current_node["children"].append(new_node)
            break
        found = False
        for child in current_node["children"]:
            if child["id"] == part:
                current_node = child
                found = True
                break
        if not found:
            new_node = {
                "id": part if part != "summary.json" else "no_children",
                "text": part if part != "summary.json" else "no_children",
                "children": []
            }
            if current_node["id"]:
                new_node["id"] = f"{current_node['id']}**{part}"
            current_node["children"].append(new_node)
            current_node = new_node


def graph_option_builder(list_of_paths, common_prefix):
    """
    returns a list of dictionary like below for the list ['03-25-2024_18-25-46-725/TC_Pair/summary.json']
    [
      {
        "id": "03-25-2024_18-25-46-725",
        "text": "03-25-2024_18-25-46-725",
        "children": [
          {
            "id": "03-25-2024_18-25-46-725**TC_Pair",
            "text": "TC_Pair",
            "children": [
              {
                "id": "03-25-2024_18-25-46-725**TC_Pair**current_heap_used",
                "text": "current_heap_used"
              },
              {
                "id": "03-25-2024_18-25-46-725**TC_Pair**reboot_count",
                "text": "reboot_count"
              }
            ]
          }
        ]
      }
    ]
    """
    tree_structure = {"id": "", "text": "", "children": []}
    for path in list_of_paths:
        add_path_to_tree(path, tree_structure, common_prefix=common_prefix)
    return tree_structure.get("children")

def build_analytics_json(summary_json):
    analytics_json = {}
    for analytic in summary_json.get("test_summary_record").get("analytics_parameters"):
        analytics_json.update({analytic: {}})
    list_iteration_data = summary_json.get("list_of_iteration_records")
    for iteration_data in list_iteration_data:
        analytics_keys = iteration_data.get("iteration_data").get("iteration_tc_analytics_data").keys()
        for analytics_key in analytics_keys:
            try:
                if iteration_data["iteration_data"]["iteration_tc_analytics_data"][analytics_key] != {}:
                    analytics_json[analytics_key].update(
                        {iteration_data["iteration_number"]: iteration_data["iteration_data"]
                        ["iteration_tc_analytics_data"][analytics_key]})
            except Exception as e:
                logging.error(e, exc_info=True)
    return analytics_json


def iteration_duration_finder(iteration_data: dict):
    try:
        begin_time = iteration_data.get("iteration_data").get("iteration_tc_execution_data").get("iteration_begin_time")
        end_time = iteration_data.get("iteration_data").get("iteration_tc_execution_data").get("iteration_end_time")
        time_difference = (datetime.datetime.strptime(end_time, "%d/%m/%Y %H:%M:%S") -
                           datetime.datetime.strptime(begin_time, "%d/%m/%Y %H:%M:%S")).total_seconds()
        return time_difference
    except Exception as e:
        logging.error(e, exc_info=True)
        return "Timing was not captured properly"
