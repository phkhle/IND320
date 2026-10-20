
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


# ============================================================
# 1. CREATE SPARK SESSION
# ============================================================

spark = (
    SparkSession.builder
    .appName("ENTSOE_Real_Data")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.cassandra.connection.host", "cassandra-db")
    .config("spark.cassandra.output.concurrent.writes", "1")
    .config("spark.cassandra.output.batch.size.rows", "20")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# ============================================================
# 2. READ HISTORICAL ENTSO-E CSV FILES
# ============================================================

print("\n=== READING ENTSO-E CSV FILES ===")

df_raw = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("/tmp/entsoe/*.csv")
)

print("\n=== RAW DATA SCHEMA ===")
df_raw.printSchema()


# ============================================================
# 3. PREPARE DATA FOR CASSANDRA
# ============================================================

df = (
    df_raw
    .withColumn("time_utc", F.to_timestamp("timestamp"))
    .select(
        F.col("connection").cast("string"),
        F.col("time_utc"),
        F.col("import_mwh").cast("double"),
        F.col("export_mwh").cast("double")
    )
)

print("\n=== PREPARED DATA SCHEMA ===")
df.printSchema()

total_rows = df.count()

print("\n=== TOTAL OBSERVATIONS ===")
print("Total rows:", total_rows)


# ============================================================
# 4. ROWS PER CONNECTION
# ============================================================

print("\n=== ROWS PER CONNECTION ===")

df.groupBy("connection").count().orderBy("connection").show(
    truncate=False
)


# ============================================================
# 5. DATA QUALITY CHECK
# ============================================================

print("\n=== DATA QUALITY CHECK ===")

# Check missing values
missing = df.select([
    F.count(
        F.when(F.col(c).isNull(), 1)
    ).alias(c)
    for c in df.columns
])

missing.show()

# Check duplicate primary keys
duplicates = (
    df.groupBy("connection", "time_utc")
    .count()
    .filter(F.col("count") > 1)
)

duplicate_count = duplicates.count()

print("Duplicate primary keys:", duplicate_count)

# Check time coverage
print("\n=== TIME COVERAGE ===")

df.groupBy("connection").agg(
    F.min("time_utc").alias("start"),
    F.max("time_utc").alias("end")
).orderBy("connection").show(truncate=False)

# Stop if data quality checks fail
missing_count = df.filter(
    F.col("connection").isNull()
    | F.col("time_utc").isNull()
    | F.col("import_mwh").isNull()
    | F.col("export_mwh").isNull()
).count()

if missing_count > 0:
    raise ValueError(
        f"Dataset contains {missing_count} rows with missing values"
    )

if duplicate_count > 0:
    raise ValueError(
        f"Dataset contains {duplicate_count} duplicate primary keys"
    )

print("\nData quality checks passed!")


# ============================================================
# 6. WRITE REAL ENTSO-E DATA TO CASSANDRA
# ============================================================

print("\n=== WRITING DATA TO CASSANDRA ===")

# Reduce parallel writes to avoid overloading Cassandra
df_write = df.coalesce(2)

(
    df_write.write
    .format("org.apache.spark.sql.cassandra")
    .mode("append")
    .options(
        table="entsoe_real",
        keyspace="ind320"
    )
    .save()
)

print("\nData successfully written to Cassandra!")


# ============================================================
# 7. READ DATA BACK FROM CASSANDRA
# ============================================================

print("\n=== READING DATA BACK FROM CASSANDRA ===")

df_cassandra = (
    spark.read
    .format("org.apache.spark.sql.cassandra")
    .options(
        table="entsoe_real",
        keyspace="ind320"
    )
    .load()
)

print("\n=== CASSANDRA ROW COUNT ===")

cassandra_count = df_cassandra.count()

print("Expected rows:", total_rows)
print("Cassandra rows:", cassandra_count)

if cassandra_count == total_rows:
    print("SUCCESS: All observations are stored in Cassandra!")
else:
    print(
        "WARNING: Cassandra row count does not match the source data!"
    )


# ============================================================
# 8. STOP SPARK
# ============================================================

spark.stop()

print("\nENTSO-E Spark pipeline completed!")
