import pandas as pd
import os

dfs = []
for file in os.listdir('./dataset'):
    df = pd.read_parquet('./dataset/' + file)
    print(df.shape)
    dfs.append(df)
    break
dataset = pd.concat(dfs)
dataset.to_csv('small_dataset.csv')
