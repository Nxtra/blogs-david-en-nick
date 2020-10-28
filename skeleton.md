# Serverless data transform with kinesis

![architecture](./img/architecture.png)

## What are we trying to do here (David)

The goal of this blog is to explore the use of Amazon Kinesis Data Firehose service to load raw streaming data events on an Amazon S3 bucket (thus creating a data lake) in a format that lends itself to efficient batch processing of those events, to allow for the analysis and visualization of the streaming data over longer time frames.

The source data used for this purpose is traffic data, pulled from an API of the governement of Flanders (verwijzing naar vorige blog?) -- uitleg batch vs real time invoegen --, which will be transformed into an easily queryable format using an ETL workflow.

To implement such an ETL workflow using AWS services, multiple approaches are  possible. It is, for example, possible to implement the ETL flow using the AWS Data Pipeline service in concert with the the Amazon EMR service. However, this approach - which could be labeled as a 'traditional' approach - is not easy to implement and furthermore is not serverless, thus requiring management of the underlying infrastructure. The introduction, in recent years, of serverless AWS services (e.g. AWS Glue, AWS step functions, AWS Lambda,...) however, has made it possible to achieve a completely serverless ETL workflow with reduced complexity from an implementational an management viewpoint.

In the following we will explore and compare the different serverless AWS services options that are currently available and also discuss the considerations that should be taken into account with regard to the choice of data format to be used in the data lake (e.g. access pattern and partitioning of the data).  


<!-- - land raw events on s3
- create a data lake on s3 to query on
- create a data lake in a queryable format
- think about access pattern and partitioning -->

## Landing data on s3 with Kinesis Firehose
As already mentioned, our goal is to land our data on an S3 bucket. Luckily, Amazon provides two managed solutions which will allow us to achieve this. These services, called AWS Kinesis Firehose and AWS Kinesis Data Streams, can be used to load data into AWS data stores. 

Next we will discuss the differences between these solutions and explain the choice to use Kinesis Firehose. 

<!--- We want to land our data on an S3 bucket.  
We should praise ourselves lucky cause AWS has a managed solution for that!  
AWS Kinesis Firehose loads data into AWS data stores. --> 

### Kinesis data streams vs Kinesis firehose
AWS Kinesis Firehose and AWS Kinesis Data Streams offer a similar, yet different solution to land data on an S3 bucket.

Let's explore the differences between these services. 
<!---I told you we are going to use AWS Kinesis Firehose. 
However, AWS also offers a similar, yet different solution: AWS Kinesis data streams. 
Let's find out what the differences are. --> 

#### Kinesis Data Streams Properties
- Millisecond latency: used for realtime analytics and actions.
- Order is preserved per shard.
- Not completely serverless: you have to manage the amount of shards yourself.
- Secure durable storage of events on the stream up to 7 days.
- Can be digested with a Lambda function.

TODO - wat wordt er bedoeld met 'You have to manage the shards yourself which you can automate by using the Streams API.'?
<!---> Data Streams are for milliseconds realtime analytics.
> You have to manage the shards yourself which you can automate by using the Streams API. --> 

#### Kinesis Firehose Properties
- Completely serverless solution.
- Buffer size of 1 to 128 MiBs and a buffer interval of 60 to 900 seconds.
- Direct-to-data-store integration with S3, RedShift, ElasticSearch..
- Can convert record format before landing them in the datastore.


Since the current use case is to ingest the data, then convert it to the "parquet" format and finally to land it on an S3 bucket for further batch processing, Kinesis Firehose is the service whose properties are best suited.
<!---> Data Firehose is completely serverless and can be used for near realtime application. 

<!---In our case we want to ingest the data, convert it to the `parquet` format and land the data on S3 in order to do further batch processing.
Hence, this is a use case for Kinesis Firehose. --> 

## Transform and land the data

### converting / transforming the data format (David)
There are two main considerations which led to the choice of using the parquet file format, a columnar data storage format, for storing the data on S3.

Firstly, the parquet format provides efficient data compression, leading to a reduction of the storage that is required. The amount of storage that is saved, will especially become more noticeable as the amount of data to be stored increases.  

Secondly, this format is optimized for query performance, which means that amount of data being scanned during querying will be siginificantly less (as compared to querying data in, e.g., the JSON format). This will result in reduced costs when the data is queried for further batch processing.

<!--- From json to parquet -->
<!--- The first consideration is query efficiency. 
- Why?
  - Better queryable
  - Less storage needed --> 

### Partitioning using firehose
As mentioned directly above using Kinesis Firehose allows us to transform the format of the records to parquet before landing the data on S3.

Next, let's look at the manner in which the data is organised on S3. 

<!---Okay, we can transform the record format before landing the data on S3.  
Let's now look at how the data is organised on S3.

<!--Amazon Kinesis Data Firehose uses a UTC time prefix (`YYYY/MM/DD/HH`) to organize the data when landing it on S3.
You could make the analogy with folders, though S3 doesn't work with folders.
It uses keys (here separated by a `/`) to differ the path on which an object can be found on S3.

<!--A couple of consequences:
- Data is partitioned by Year, Month, Day, Hour (in that order).
- Firehose uses UTC time to generate the value of the partitions.
- The time used to create the partitions is the time at which the data is processed by firehose.
- You cannot directly use a time that was specified in the event to land the data in a partition.

<!-- > Firehose uses the processing time to create partitions on S3; You cannot use a timestamp that comes directly from your data.

<!--Luckily, in our next blog, we will see how to repartition your data on S3 in order to organize events by a timestamp coming from the data in the event itself.

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
