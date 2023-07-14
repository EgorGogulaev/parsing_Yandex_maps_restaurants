import pandas as pd
import glob

path = glob.glob('data_final/*')

df = pd.concat((pd.read_excel(file) for file in path), ignore_index=True)
df = df.drop_duplicates(subset=['Яндекс ссылка'], keep='first')
df.reset_index(inplace=True)
df.drop('index', axis=1, inplace=True)
df.to_excel('./data/data.xlsx', index=False)
print(df)