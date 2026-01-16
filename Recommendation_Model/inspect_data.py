import pandas as pd

try:
    df = pd.read_csv('EG ACC REOPRT 2.csv')
    with open('columns.txt', 'w') as f:
        f.write(f"Columns: {list(df.columns)}\n")
        f.write(f"First row: {df.iloc[0].to_dict()}\n")
        f.write(f"Info:\n")
        df.info(buf=f)
except Exception as e:
    print(f"Error reading CSV: {e}")
