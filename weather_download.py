
import pandas as pd
from pathlib import Path
import requests
import time


def get_era5_weather(latitude, longitude, start_date, end_date):
    """
    Download hourly ERA5 reanalysis weather data
    for a single geographic location.
    """

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "models": "era5",
        "timezone": "UTC"
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    # The response is expected to be in JSON format, and we extract the "hourly" data
    data = response.json()["hourly"]

    df = pd.DataFrame(data)
    # Convert the "time" column to datetime format with UTC timezone
    df["time"] = pd.to_datetime(df["time"], utc=True)

    return df




def download_region_weather(
    region,
    start_date,
    end_date,
    n_locations=1000
):
    """
    Download hourly ERA5 weather data for a selected region.

    Coordinates are loaded from a previously generated CSV file.
    """

    # Load sampled locations
    project_root = Path(__file__).resolve().parent

    locations_path = (
        project_root
        / "data"
        / "geography"
        / "weather_locations.csv"
    )

    locations = pd.read_csv(locations_path)

    # Select coordinates for the requested region
    region_points = locations.loc[
        locations["region"] == region
    ].head(n_locations)

    if region_points.empty:
        raise ValueError(f"No locations found for {region}")

    results = []

    for _, point in region_points.iterrows():

        weather = get_era5_weather(
            latitude=point["latitude"],
            longitude=point["longitude"],
            start_date=start_date,
            end_date=end_date
        )

        weather["region"] = region
        weather["point_id"] = point["point_id"]

        results.append(weather)

    return pd.concat(results, ignore_index=True)



def download_and_save_region_weather(
    region,
    start_date,
    end_date,
    locations=None,
    batch_size=10,
    n_locations=None,
    output_dir=None
):
    """
    Download ERA5 weather data in batches.
    Save each completed batch and skip it on future runs.
    """

    project_root = Path(__file__).resolve().parent

    if locations is None:
        locations = pd.read_csv(
            project_root / "data" / "geography" / "weather_locations.csv"
        )

    if output_dir is None:
        output_dir = project_root / "data" / "weather"



    points = locations.loc[
        locations["region"] == region
    ].copy()

    if n_locations is not None:
        points = points.head(n_locations)

    if points.empty:
        raise ValueError(f"No locations found for {region}")

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    output_path = Path(output_dir) / region
    output_path.mkdir(parents=True, exist_ok=True)

    url = "https://archive-api.open-meteo.com/v1/archive"

    for start in range(0, len(points), batch_size):

        batch = points.iloc[start:start + batch_size]

        # Include dates and point IDs to avoid mixing datasets
        first_id = batch["point_id"].iloc[0]
        last_id = batch["point_id"].iloc[-1]

        filename = (
            f"{region}_{start_date}_{end_date}_"
            f"{first_id}_{last_id}.parquet"
        )

        filepath = output_path / filename

        # Skip previously completed batches
        if filepath.exists():
            print(f"Already saved: {filename}")
            continue

        params = {
            "latitude": ",".join(
                batch["latitude"].astype(str)
            ),
            "longitude": ",".join(
                batch["longitude"].astype(str)
            ),
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,precipitation",
            "models": "era5",
            "timezone": "UTC"
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=120
            )

            if response.status_code == 429:
                raise RuntimeError(
                    "Open-Meteo API limit reached (HTTP 429). "
                    "Completed batches have been saved. "
                    "Please try again later."
                )
            
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as error:
            raise RuntimeError(
                f"Weather download interrupted: {error}. "
                "Completed batches have been saved."
            ) from error

        if isinstance(data, dict):
            data = [data]

        if len(data) != len(batch):
            raise ValueError("Unexpected API response count")

        results = []

        for (_, point), location_data in zip(
            batch.iterrows(), data
        ):
            df = pd.DataFrame(location_data["hourly"])

            df["time"] = pd.to_datetime(
                df["time"], utc=True
            )
            df["region"] = region
            df["point_id"] = point["point_id"]

            results.append(df)

        batch_df = pd.concat(results, ignore_index=True)

        # Save completed batch
        batch_df.to_parquet(filepath, index=False)

        print(
            f"Saved {min(start + batch_size, len(points))}"
            f"/{len(points)} locations"
        )

        time.sleep(1)

    print("Download run finished.")
    
        # Combine downloaded batches
    print("Starting aggregation...")

        # Combine downloaded batches
    batch_files = []

    for start in range(0, len(points), batch_size):
        batch = points.iloc[start:start + batch_size]

        first_id = batch["point_id"].iloc[0]
        last_id = batch["point_id"].iloc[-1]

        filename = (
            f"{region}_{start_date}_{end_date}_"
            f"{first_id}_{last_id}.parquet"
        )

        batch_files.append(output_path / filename)

    df = pd.concat(
        [pd.read_parquet(file) for file in batch_files],
        ignore_index=True
    )

    # Calculate hourly spatial averages
    df_hourly = (
    df.groupby("time", as_index=False)
    .agg(
        temperature_mean=("temperature_2m", "mean"),
        precipitation_mean=("precipitation", "mean"),
        n_locations=("point_id", "nunique")
    )
)

    # Save aggregated weather data
    final_path = (
        project_root
        / "data"
        / "weather"
        / f"{region}_hourly_mean_2024.parquet"
    )

    df_hourly.to_parquet(final_path, index=False)

    print(f"Aggregated weather data saved: {final_path}")

    return final_path


