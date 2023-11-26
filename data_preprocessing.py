import os
import re
from solcx import compile_standard, install_solc
import sys
import pandas as pd

available_versions = ['0.5.0', '0.5.1', '0.5.2', '0.5.3', '0.5.4', '0.5.5', '0.5.6', '0.5.7', '0.5.8', '0.5.9',
                      '0.5.10', '0.5.11', '0.5.12', '0.5.13', '0.5.14', '0.5.15', '0.5.16', '0.5.17',
                      '0.6.0', '0.6.1', '0.6.2', '0.6.3', '0.6.4', '0.6.5', '0.6.6', '0.6.7', '0.6.8', '0.6.9',
                      '0.6.10', '0.6.11', '0.6.12', '0.7.0', '0.7.6',
                      '0.8.2', '0.8.3', '0.8.4', '0.8.5', '0.8.6', '0.8.7', '0.8.8', '0.8.9', '0.8.10',
                      '0.8.11', '0.8.12', '0.8.13', '0.8.14', '0.8.15', '0.8.16', '0.8.17', '0.8.18',
                      '0.8.19', '0.8.20', '0.8.21', '0.8.22', '0.8.23']


def remove_comments(string):
    pattern = r"(\".*?\"|\'.*?\')|((?s)/\*.*?\*/)|(//[^\r\n]*$)"
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        if match.group(2) is not None:
            return " "
        else:
            return match.group(1) or match.group(3)

    return regex.sub(_replacer, string)


def get_version(versions):
    if len(versions) > 0 and versions[0] in available_versions:
        return versions[0]
    else:
        return -1


def preprocess(df):
    for i in range(df.shape[0]):
        addr, sc, bc = df.iloc[i]['contracts'], df.iloc[i]['source_code'], df.iloc[i]['bytecode']
        for line in sc.split('\n'):
            res = remove_comments(line)
            if not res.isspace() and len(res) != 0:
                # solidity version definition position
                def_pos = res.find('pragma solidity')
                if def_pos != -1:
                    version_demand = res[def_pos + len('pragma solidity'):-1]
                    versions = re.findall('\d+\.\d+\.\d+', version_demand)
                    version = get_version(versions)
                    if version == -1:
                        break
                    try:
                        with open(f'./asm_final/source/sol/{addr}.sol', 'w') as f:
                            f.write(sc)
                        with open(f'./asm_final/source/versions/{addr}.txt', 'w') as f:
                            f.write(version)
                        os.system(f'solc-select use {version}')
                        print(os.system(f'solc --asm ./asm_final/source/sol/{addr}.sol > ./asm_final/source/asm/{addr}.asm'))
                        print(os.system(f'solc --asm --optimize ./asm_final/source/sol/{addr}.sol > ./asm_final/source/asm/{addr}.asm'))
                    except Exception as e:
                        print(e)


if __name__ == '__main__':
    dataset_path = './dataset'
    for file in os.listdir(dataset_path):
        df = pd.read_parquet(file)
