# Serverless data transform with kinesis

![architecture](./img/architecture.png)

## What are we trying to do here (David)

- land raw events on s3
- create a data lake on s3 to query on
- create a data lake in a queryable format
- think about access pattern and partitioning

## Landing data on s3 with Kinesis Firehose

We want to land our data on an S3 bucket.  
We should praise ourselves lucky cause AWS has a managed solution for that!  
AWS Kinesis Firehose loads data into AWS data stores.

### Kinesis data streams vs Kinesis firehose
I told you we are going to use AWS Kinesis Firehose. 
However, AWS also offers a similar, yet different solution: AWS Kinesis data streams. 
Let's find out what the differences are.

#### Kinesis Data Streams
- Millisecond latency: used for realtime analytics and actions.
- Order is preserved per shard.
- Not completely serverless: you have to manage the amount of shards yourself.
- Secure durable storage of events on the stream up to 7 days.
- Can be digested with a Lambda function.

> Data Streams are for milliseconds realtime analytics.
> You have to manage the shards yourself which you can automate by using the Streams API.

#### Kinesis Firehose
- Completely serverless solution.
- Buffer size of 1 to 128 MiBs and a buffer interval of 60 to 900 seconds.
- Direct-to-data-store integration with S3, RedShift, ElasticSearch..
- Can convert record format before landing them in the datastore.

> Data Firehose is completely serverless and can be used for near realtime application. 

In our case we want to ingest the data, convert it to the `parquet` format and land the data on S3 in order to do further batch processing.
Hence, this is a use case for Kinesis Firehose.

## Transform and land the data

### converting / transforming the data format (David)

From json to parquet

- Why?
  - Better queryable
  - Less storage neede

### Partitioning using firehose
Okay, we can transform the record format before landing the data on S3.  
Let's now look at how the data is organised on S3.

Amazon Kinesis Data Firehose uses a UTC time prefix (`YYYY/MM/DD/HH`) to organize the data when landing it on S3.
You could make the analogy with folders, though S3 doesn't work with folders.
It uses keys (here separated by a `/`) to differ the path on which an object can be found on S3.

A couple of consequences:
- Data is partitioned by Year, Month, Day, Hour (in that order).
- Firehose uses UTC time to generate the value of the partitions.
- The time used to create the partitions is the time at which the data is processed by firehose.
- You cannot directly use a time that was specified in the event to land the data in a partition.

> Firehose uses the processing time to create partitions on S3; You cannot use a timestamp that comes directly from your data.

Luckily, in our next blog, we will see how to repartition your data on S3 in order to organize events by a timestamp coming from the data in the event itself.

#### Hive
We need to be forward thinking and name our partitions on S3.
This will help us out when doing repartitioning or analysis with AWS Glue.

Firehose allows you to use the `Hive` naming convention.
Using this naming convention, data can better cataloged with AWS Glue crawlers which will result in proper partition names.

Following the `Hive` specs the folder structure is of the format “/partitionkey1=partitionvalue1/partitionkey2=partitionvalue2

In the AWS console you can specify an S3 prefix for your firehose.
Name your folders year, month, day and hour by using the following `Hive` format:
```
myOwnCustomPrefix/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/
```


# Cloudformation example?

# Conclusion (Nick + David)

We have created a datalake on s3 that is partitioned, queryable and in optimal format.
