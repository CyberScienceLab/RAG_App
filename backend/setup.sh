#!/bin/bash

# step 1, create PEN_TEST_PROJ_PATH env variable
if [ $(grep -c "PEN_TEST_PROJ_PATH" ~/.bashrc) -eq 0 ]; then
    {
        echo
        echo "# added by setup.sh in RAG_App"
        echo export PEN_TEST_PROJ_PATH=$(pwd)/Penetration_Testing_RAG/
        echo
    } >> ~/.bashrc

    echo "Successfully created env variable PEN_TEST_PROJ_PATH."
else
    echo "env variable PEN_TEST_PROJ_PATH already exists."
fi


# All new RAGs must be added here, with their exact project name
rag_list=(
    "Penetration_Testing_Rag" 
    "Malware_Analysis_Rag" 
    "Threat_Intelligence_Rag"
)

# clone and install all dependencies for each rag
for rag_name in "${rag_list[@]}"
do 
    if [ -d "$rag_name" ]; then
        echo "Directory $rag_name already exists."
    else
        git clone "https://github.com/CyberScienceLab/$rag_name.git" "$rag_name"
        pip install -r "$rag_name/requirements.txt"
        
        echo "Successfully setup $rag_name"
    fi
done

pip install -r requirements.txt
