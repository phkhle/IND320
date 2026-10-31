
import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


# ============================================================
# 1. INITIALIZE SPARK
# ============================================================

spark = (
    SparkSession.builder
    .appName("ENTSOE_Export_Daily")
    .master("local[1]")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.cassandra.connection.host", "cassandra-db")
    .config("spark.sql.shuffle.partitions", "2")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

try:
    # ========================================================
    # 2. READ REAL ENTSO-E DATA FROM CASSANDRA
    # ========================================================

    df = (
        spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(
            table="entsoe_real",
            keyspace="ind320"
        )
        .load()
    )

    # ========================================================
    # 3. AGGREGATE BY NORWEGIAN CALENDAR DAY
    # ========================================================

    df_daily = (
        df.withColumn(
            "date",
            F.date_format(
                F.from_utc_timestamp(
                    "time_utc",
                    "Europe/Oslo"
                ),
                "yyyy-MM-dd"
            )
        )
        .groupBy("connection", "date")
        .agg(
            F.sum("import_mwh").alias("total_import_mwh"),
            F.sum("export_mwh").alias("total_export_mwh")
        )
        .orderBy("connection", "date")
    )

    # ========================================================
    # 4. VALIDATE AGGREGATED DATA
    # ========================================================

    print("\nDaily ENTSO-E data:")
    df_daily.show(10, truncate=False)

    print("\nNumber of daily records:", df_daily.count())

    # ========================================================
    # 5. CONVERT TO JSON DOCUMENTS
    # ========================================================

    documents = [
        {
            "connection": row["connection"],
            "date": row["date"],
            "total_import_mwh": float(row["total_import_mwh"]),
            "total_export_mwh": float(row["total_export_mwh"]),
            "is_test_data": False
        }
        for row in df_daily.collect()
    ]

    # ========================================================
    # 6. EXPORT TO JSON
    # ========================================================

    output_path = "/tmp/entsoe_daily.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(documents, file, indent=2)

    print(
        f"\nExported {len(documents)} daily documents "
        f"to {output_path}"
    )

finally:
    # ========================================================
    # 7. STOP SPARK
    # ========================================================

    spark.stop()
