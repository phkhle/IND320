import requests
import pandas as pd


# Give the NVE API URL
NVE_URL = (
    "https://biapi.nve.no/magasinstatistikk/"
    "api/Magasinstatistikk/HentOffentligData"
)

# Create a function to get data from the NVE API with optional start and end date filters
def get_nve_data(start_date=None, end_date=None):

    response = requests.get(NVE_URL, timeout=60)
    response.raise_for_status()

    df = pd.DataFrame(response.json())

    # Convert Date column to datetime format
    df["dato_Id"] = pd.to_datetime(df["dato_Id"])

    # Filter the DataFrame based on the provided start and end dates
    if start_date is not None:
        df = df[df["dato_Id"] >= pd.to_datetime(start_date)]

    if end_date is not None:
        df = df[df["dato_Id"] <= pd.to_datetime(end_date)]

    return df.sort_values("dato_Id").reset_index(drop=True)