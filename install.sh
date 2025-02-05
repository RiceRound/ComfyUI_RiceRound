#!/bin/bash

# Define paths relative to the current directory for requirements files
requirements_txt="$(dirname "$0")/requirements.txt"
requirements_repair_txt="$(dirname "$0")/repair_dependency_list.txt"

# Define Python executables for different environments
python_exec="../../../python_embeded/python3"
aki_python_exec="../../python/python3"

echo "Installing EasyUse Requirements..."

# Check if the ComfyUI Portable Python exists
if [ -f "$python_exec" ]; then
    echo "Installing with ComfyUI Portable"
    "$python_exec" -m pip install --upgrade pip
    "$python_exec" -m pip install -r "$requirements_txt"

# Check if the ComfyUI Aki Python exists
elif [ -f "$aki_python_exec" ]; then
    echo "Installing with ComfyUI Aki"
    "$aki_python_exec" -m pip install --upgrade pip
    "$aki_python_exec" -m pip install -r "$requirements_txt"
    
    # Attempt to install missing dependencies from the repair list
    while IFS= read -r line; do
        "$aki_python_exec" -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "$line"
    done < "$requirements_repair_txt"

# Fall back to system Python if neither of the above are found
else
    echo "Installing with system Python"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "$requirements_txt"
fi

# Wait for the user to acknowledge completion
echo "Installation completed. Press any key to continue..."
read -n 1 -s
