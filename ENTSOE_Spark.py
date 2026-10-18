
from ENTSOE_API import get_entsoe_data
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
from pyspark.sql import functions as F
import json


# 1. Get synthetic ENTSO-E data
df = get_entsoe_data(
    start_date="2026-10-01",
    end_date="2026-10-03",
    test_mode=True
)

# 2. Create Spark session
spark = (
    SparkSession.builder
    .appName("ENTSOE_Project2")
    .config("spark.cassandra.connection.host", "cassandra-db")
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()
)

# Use Norwegian timezone for Spark SQL
spark.conf.set("spark.sql.session.timeZone", "Europe/Oslo")

# 3. Convert Pandas DataFrame to Spark DataFrame
spark_df = spark.createDataFrame(df)

# 4. Prepare timestamp and columns
spark_df = spark_df.select(
    col("connection"),
    col("timestamp").cast("timestamp").alias("time_utc"),
    col("import_mwh"),
    col("export_mwh")
)

print("Spark rows:", spark_df.count())
spark_df.show(5, truncate=False)

# 5. Show data before saving
print("Spark rows:", spark_df.count())
spark_df.show(5, truncate=False)

# 6. Write Spark DataFrame to Cassandra
spark_df.write \
    .format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .options(table="entsoe_test", keyspace="ind320") \
    .save()

print("Data saved to Cassandra!")

# 7. Read data back from Cassandra
df_from_cassandra = (
    spark.read
    .format("org.apache.spark.sql.cassandra")
    .options(table="entsoe_test", keyspace="ind320")
    .load()
)

print("Rows read from Cassandra:", df_from_cassandra.count())
df_from_cassandra.show(5, truncate=False)



# Calculate total import and export per connection
summary_df = (
    df_from_cassandra
    .groupBy("connection")
    .agg(
        F.sum("import_mwh").alias("total_import_mwh"),
        F.sum("export_mwh").alias("total_export_mwh")
    )
    .orderBy("connection")
)

summary_df.show(truncate=False)


# Calculate monthly import and export per connection
monthly_df = (
    df_from_cassandra
    .withColumn("month", F.date_format("time_utc", "yyyy-MM"))
    .groupBy("connection", "month")
    .agg(
        F.sum("import_mwh").alias("total_import_mwh"),
        F.sum("export_mwh").alias("total_export_mwh")
    )
    .orderBy("connection", "month")
)

monthly_df.show(30, truncate=False)

# Convert Spark DataFrame to Python documents
monthly_documents = [
    row.asDict()
    for row in monthly_df.collect()
]

print("Number of documents:", len(monthly_documents))
print("First document:", monthly_documents[0])


with open("/tmp/entsoe_monthly_test.json", "w") as f:
    json.dump(monthly_documents, f, indent=2)

print("JSON file created!")

spark.stop()
