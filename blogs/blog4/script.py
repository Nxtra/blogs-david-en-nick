from pyspark.sql.functions import lit,col,year,month,dayofmonth,hour,to_date,from_unixtime
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
import datetime
d_time = datetime.datetime.now() - datetime.timedelta(hours=1)

glueContext = GlueContext(spark)

datasource0 = glueContext.create_dynamic_frame_from_catalog(
    database='anpr', 
    table_name="anpr_parquet_step1_with_crawlerresults",
    push_down_predicate = f"year = 2020 and month = {d_time.month} and day = {d_time.day} and hour = {d_time.hour}", 
    transformation_ctx = "datasource0")
df = datasource0.toDF()
import datetime
from pyspark.sql.functions import year, month, dayofmonth,hour

df.select(
    year("originalrecordtimestamp").alias('year'), 
    month("originalrecordtimestamp").alias('month'), 
    dayofmonth("originalrecordtimestamp").alias('day'),
    hour("originalrecordtimestamp").alias('hour')
).show()



# Executing this cell is enough to repartition the data
dyf = DynamicFrame.fromDF(repartitioned_with_new_columns_df, glueContext, "enriched")

s3_path = "s3://sls-data-pipelines-test-05-22/analytics/repartitioned_results/"
options_connect = {"path": s3_path,"partitionKeys":["year","month","day","hour"]}

## Below works
datasink = glueContext.write_dynamic_frame.from_options(frame = dyf, connection_type="S3", connection_options = options_connect , format = "parquet", transformation_ctx = "datasink5")

## I don't think the below is possible since for glue a table is a /key in s3
# datasink = glueContext.write_dynamic_frame_from_catalog(frame = dyf, database = "anpr", table_name = "repartitioned_results", transformation_ctx = "datasink")

# datasink = glueContext.write_dynamic_frame.from_catalog(frame = dyf, database = "anpr", table_name = "anpr-parquet-repartitioned", transformation_ctx = "datasink5")

# the below is also working
repartitioned_with_new_columns_df.write.partitionBy("year", "month", "day", "hour").mode(
"overwrite").parquet("s3://sls-data-pipelines-test-05-22/analytics/repartitioned_results/")

dyf = DynamicFrame.fromDF(repartitioned_with_new_columns_df, glueContext, "enriched")

applymapping1 = ApplyMapping.apply(frame = dyf  , mappings = [("uniqueid", "int", "uniqueid", "int"), ("speed", "int", "speed", "int"), ("trafficjamindicator", "int", "trafficjamindicator", "int"), ("recordtimestamp", "long", "recordtimestamp", "long"),("originalrecordtimestamp","Timestamp","originalrecordtimestamp","Timestamp"), ("year", "string", "year", "string"), ("month", "string", "month", "string"), ("day", "string", "day", "string"), ("hour", "string", "hour", "string")], transformation_ctx = "applymapping1")
selectfields2 = SelectFields.apply(frame = applymapping1, paths = ["uniqueid", "speed", "trafficjamindicator", "recordtimestamp","originalrecordtimestamp","year","month","day","hour"], transformation_ctx = "selectfields2")
resolvechoice3 = ResolveChoice.apply(frame = selectfields2, choice = "MATCH_CATALOG", database = "anpr", table_name = "anpr-parquet-repartitioned", transformation_ctx = "resolvechoice3")
resolvechoice4 = ResolveChoice.apply(frame = resolvechoice3, choice = "make_struct", transformation_ctx = "resolvechoice4")

s3_path = "s3://sls-data-pipelines-test-05-22/analytics/repartitioned_results/"
options_connect = {"path": s3_path,"partitionKeys":["year","month","day","hour"]}
datasink5 = glueContext.write_dynamic_frame.from_options(frame = dyf, connection_type="S3", connection_options = options_connect , format = "parquet", transformation_ctx = "datasink5")
# job.commit()