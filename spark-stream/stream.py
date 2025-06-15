from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, window, count, avg
from pyspark.sql.types import StructType, StringType, DoubleType, LongType

# 1️⃣ Define schema
schema = StructType() \
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

# 2️⃣ Start Spark session
spark = SparkSession.builder \
    .appName("EarthquakeStreamProcessor") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# 3️⃣ Read Kafka stream
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "earthquakes") \
    .load()

# 4️⃣ Parse Kafka stream and create event_time column
json_df = df.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", to_timestamp("time_str"))

# 5️⃣ High magnitude filter
high_mag = json_df.filter(col("magnitude") > 1.0)

# 6️⃣ Aggregation: quake count and avg magnitude per 10-min window
agg_df = json_df \
    .withWatermark("event_time", "30 minutes") \
    .groupBy(window(col("event_time"), "10 minutes")) \
    .agg(
        count("*").alias("quake_count"),
        avg("magnitude").alias("avg_magnitude")
    )

# 7️⃣ File sink to store raw stream (CSV format)
file_sink = json_df.writeStream \
    .format("csv") \
    .option("path", "output/earthquake_stream") \
    .option("checkpointLocation", "checkpoints/earthquake_stream") \
    .outputMode("append") \
    .start()

# 8️⃣ Console sink for high magnitude alerts
console_highmag = high_mag.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# 9️⃣ Console sink for aggregated stats
console_agg = agg_df.writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# 🔟 Await all queries
spark.streams.awaitAnyTermination()
