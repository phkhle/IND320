from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Create SparkSession with limited resources
spark = (
    SparkSession.builder
    .appName("ENTSOE_Complete_Cassandra")
    .master("local[1]")
    .config("spark.driver.memory", "768m")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.cassandra.connection.host", "cassandra-db")
    .config("spark.cassandra.output.concurrent.writes", "1")
    .config("spark.cassandra.output.batch.size.rows", "20")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("SparkSession started!")

def load_month(month):
    """
    Load ENTSO-E data for a single month from a CSV file.

    Returns
    pyspark.sql.DataFrame
        Monthly electricity flow data.
    """

    # Define the CSV file path
    file_path = f"/tmp/entsoe/entsoe_{month}.csv"

    # Read the CSV file using an explicit schema
    df = (
        spark.read
        .option("header", True)
        .schema(
            "timestamp string, connection string, "
            "import_mwh double, export_mwh double"
        )
        .csv(file_path)
    )

    # Convert the timestamp and select the required columns
    df = (
        df.withColumn("time_utc", F.to_timestamp("timestamp"))
        .select(
            "connection",
            "time_utc",
            "import_mwh",
            "export_mwh"
        )
    )

    return df

def write_batch_to_cassandra(df):
    """
    Write a small batch of ENTSO-E observations to Cassandra.

    Existing rows with the same primary key will be updated,
    while missing rows will be inserted.
    """

    (
        df.coalesce(1)
        .write
        .format("org.apache.spark.sql.cassandra")
        .mode("append")
        .options(
            table="entsoe_real",
            keyspace="ind320"
        )
        .save()
    )


def write_month_to_cassandra(month, batch_size=1000):
    """
    Process one month of ENTSO-E data and write it to Cassandra
    in small batches to reduce memory usage.
    """

    df = load_month(month)

    # Collect only one month of data for controlled batching
    rows = df.collect()
    total_rows = len(rows)

    print(f"Processing {month}: {total_rows} observations")

    # Split the monthly data into small batches
    for start in range(0, total_rows, batch_size):

        batch = rows[start:start + batch_size]

        # Create a Spark DataFrame with the original schema
        batch_df = spark.createDataFrame(batch, schema=df.schema)

        # Write the batch to Cassandra
        write_batch_to_cassandra(batch_df)

        print(
            f"{month}: {min(start + batch_size, total_rows)}"
            f"/{total_rows} observations processed"
        )

    print(f"Completed: {month}")

# if __name__ == "__main__":
#     try:
#         # Process all months from January 2024 to December 2025
#         for year in [2024, 2025]:
#             for month in range(1, 13):

#                 month_str = f"{year}-{month:02d}"

#                 print(f"\nStarting: {month_str}")

#                 write_month_to_cassandra(
#                     month=month_str,
#                     batch_size=1000
#                 )

#         print("\nAll 24 months processed successfully!")

#     finally:
#         # Release Spark resources
#         spark.stop()

if __name__ == "__main__":
    try:
        # Resume processing from April 2025
        months = [
            f"2025-{month:02d}"
            for month in range(4, 13)
        ]

        for month in months:
            print(f"\nStarting: {month}")

            write_month_to_cassandra(
                month=month,
                batch_size=500
            )

        print("\nAll remaining months processed successfully!")

    finally:
        # Release Spark resources
        spark.stop()