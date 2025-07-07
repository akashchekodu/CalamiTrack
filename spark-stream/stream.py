from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, window, count, avg
from pyspark.sql.types import StructType, StringType, DoubleType, LongType

# Spark session
spark = SparkSession.builder \
    .appName("MultiHazardStreamProcessor") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# 🟠 Earthquake schema
eq_schema = StructType() \
    .add("id", StringType()) \
    .add("place", StringType()) \
    .add("magnitude", DoubleType()) \
    .add("magType", StringType()) \
    .add("time", LongType()) \
    .add("time_str", StringType()) \
    .add("longitude", DoubleType()) \
    .add("latitude", DoubleType()) \
    .add("depth", DoubleType()) \
    .add("tsunami", StringType()) \
    .add("sig", DoubleType()) \
    .add("type", StringType()) \
    .add("status", StringType()) \
    .add("gap", DoubleType()) \
    .add("rms", DoubleType())

# 🔴 Wildfire schema (VIIRS)
fire_schema = StructType() \
    .add("latitude", DoubleType()) \
    .add("longitude", DoubleType()) \
    .add("brightness", DoubleType()) \
    .add("scan", DoubleType()) \
    .add("track", DoubleType()) \
    .add("acq_date", StringType()) \
    .add("acq_time", StringType()) \
    .add("satellite", StringType()) \
    .add("confidence", StringType()) \
    .add("version", StringType()) \
    .add("type", StringType()) \
    .add("daynight", StringType()) \
    .add("location", StringType())

# 📡 Read Earthquake Kafka stream
eq_stream = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "earthquakes") \
    .load()

eq_df = eq_stream.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), eq_schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", to_timestamp("time_str"))

# 📡 Read Wildfire Kafka stream
fire_stream = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "wildfires") \
    .load()

fire_df = fire_stream.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), fire_schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", to_timestamp("acq_date", "yyyy-MM-dd"))

# 💾 Write Earthquake Stream to Disk
eq_sink = eq_df.writeStream \
    .format("csv") \
    .option("path", "output/earthquake_stream") \
    .option("checkpointLocation", "checkpoints/earthquake_stream") \
    .outputMode("append") \
    .start()

# 💾 Write Wildfire Stream to Disk
fire_sink = fire_df.writeStream \
    .format("csv") \
    .option("path", "output/wildfire_stream") \
    .option("checkpointLocation", "checkpoints/wildfire_stream") \
    .outputMode("append") \
    .start()

# 🖥️ Optional: Console output for monitoring
console_eq = eq_df.filter(col("magnitude") > 3.5).writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

console_fire = fire_df.filter(col("confidence") == "nominal").writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# ⏳ Wait
spark.streams.awaitAnyTermination()
