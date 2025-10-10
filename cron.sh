SHELL=/bin/bash
PYTHON_PATH=/usr/bin/
PROJECT_PATH=/root/trading/AssetAllocation
0 15 * * * ${PYTHON_PATH}python3 ${PROJECT_PATH}/run.py -caa -lsa >> ${PROJECT_PATH}/overseas.log 2>&1
