import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


# Initialize Spark
spark = (
    SparkSession.builder
    .appName("ENTSOE_Export_MongoDB")
    .master("local[1]")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.cassandra.connection.host", "cassandra-db")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

try:
    # Read historical electricity flows from Cassandra
    df = (
        spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(table="entsoe_real", keyspace="ind320")
        .load()
    )

    # Aggregate electricity flows by Norwegian calendar month
    df_monthly = (
        df.withColumn(
            "month",
            F.date_format(
                F.from_utc_timestamp("time_utc", "Europe/Oslo"),
                "yyyy-MM"
            )
        )
        .groupBy("connection", "month")
        .agg(
            F.sum("import_mwh").alias("total_import_mwh"),
            F.sum("export_mwh").alias("total_export_mwh")
        )
    )

    # Convert Spark rows into JSON-compatible documents
    documents = [
        {
            "connection": row["connection"],
            "month": row["month"],
            "total_import_mwh": float(row["total_import_mwh"]),
            "total_export_mwh": float(row["total_export_mwh"]),
            "is_test_data": False
        }
        for row in df_monthly.collect()
    ]

    # Validate the number of monthly documents
    if len(documents) != 216:
        raise ValueError(
            f"Expected 216 documents, found {len(documents)}"
        )

    # Export documents to a JSON file
    output_path = "/tmp/entsoe_monthly.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(documents, file, indent=2)

    print(f"Exported {len(documents)} documents to {output_path}")

finally:
    # Release Spark resources
    spark.stop()