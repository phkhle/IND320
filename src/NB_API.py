import requests
import pandas as pd
from io import StringIO



NB_URL = (
    "https://data.norges-bank.no/api/data/"
    "EXR/B.EUR+USD.NOK.SP"
)

def get_eur_usd_data(start_date, end_date):
    """
    Retrieve daily EUR and USD exchange rates from
    Norges Bank and calculate the EUR/USD exchange rate.
    """

    # API parameters
    params = {
        "format": "csvfile",
        "startPeriod": start_date,
        "endPeriod": end_date,
        "locale": "en"
    }

    # Retrieve data
    response = requests.get(
        NB_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    # Convert CSV response to DataFrame
    df = pd.read_csv(StringIO(response.text))

    # Convert data types
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])

    df["OBS_VALUE"] = pd.to_numeric(
        df["OBS_VALUE"],
        errors="coerce"
    )

    # One column per currency
    df = df.pivot(
        index="TIME_PERIOD",
        columns="BASE_CUR",
        values="OBS_VALUE"
    ).reset_index()

    # Rename columns
    df = df.rename(columns={
        "TIME_PERIOD": "date",
        "EUR": "EUR_NOK",
        "USD": "USD_NOK"
    })

    df.columns.name = None

    # Calculate EUR/USD
    df["EUR_USD"] = df["EUR_NOK"] / df["USD_NOK"]

    return df.sort_values("date").reset_index(drop=True)