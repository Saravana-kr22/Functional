#!/bin/bash

# Initialize variables
PYTHON_ENV_PATH=""
SCRIPT_DIR=""
SCRIPT_NAME=""
ARGUMENTS=""

# Function to display usage and exit
usage() {
    echo "Usage: $0 -python_environment <path/of/python/environment> -script_name <python script with .py> -script_arguments <arguments for Python script> -python_script_path <path to reliability test cases>"
    exit 1
}

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    -python_environment)
      PYTHON_ENV_PATH="$2"
      shift
      shift
      ;;
    -script_name)
      SCRIPT_NAME="$2"
      shift
      shift
      ;;
    -script_arguments)
      ARGUMENTS="$2"
      shift
      shift
      ;;
    -python_script_path)
      SCRIPT_DIR="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
        usage
            ;;
  esac
done


# Check if all flags are provided
if [ -z "$PYTHON_ENV_PATH" ] || [ -z "$SCRIPT_DIR" ] || [ -z "$SCRIPT_NAME" ] || [ -z "$ARGUMENTS" ]; then
    echo "Error: Missing one or more required flags."
    usage
fi

#code to clean ARGUMENTS from pattern that looks like this :-:

# Remove curly braces and commas
cleaned_input=$(echo "$ARGUMENTS" | tr -d '{},')


formatted_input=$(echo "$cleaned_input" | sed 's/:-:/ /g;')

# Navigate to the Python environment
cd "$PYTHON_ENV_PATH"

# Activate the virtual environment
source bin/activate

cd $SCRIPT_DIR

pwd

rm -rf /tmp/chip_* && rm -rf admin_storage.json && python $SCRIPT_NAME $formatted_input

# Deactivate the virtual environment (optional)
deactivate
