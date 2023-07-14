from model import *
import pandas as pd

def get_all_data():

    with engine.connect() as connection:
        result = connection.execute(Info.__table__.select())
        df_info = pd.DataFrame(result.fetchall(), columns=result.keys())
    df_info = df_info.drop('id', axis=1)
    df_info = df_info.fillna('')
    df_info = df_info.astype('str')

    return df_info
