# Serverless data pipelines: ETL workfow with Step Functions and Athena
This blog is Part 3 of a multi-part series around analysing Flanders’ traffic whilst leveraging the power of cloud components!    
For part 1 see: https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d  
For part 2 see: https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409  

# What is our goal?
The goal of this blog to explore the use of the AWS Glue service in conjunction with the AWS Athena service in order to repartition raw streaming data events. We previously landed these events on an Amazon S3 bucket partitioned according to the processing time on Kinesis. Now, however, we would like to have these events partitioned according to event timestamps to allow for meaningful batch analysis.    

# First, a short introduction to AWS Glue
AWS Glue (which was introduced in august 2017) is a serverless Extract, Transform and Load (ETL) cloud-optimized service. This service can used be used to automate ETL processes that organize, locate, move and transform data sets stored within a variety of data sources, allowing users to efficiently prepare these datasets for data analysis. These data sources can e.g., be data lakes in Amazon Simple Storage Service (S3), data warehouses in Amazon Redshift or other databases that are part of the Amazon Relational Database Service. Other types of databases such as MySQL, Oracle, Microsoft SQL Server and PostgreSQL are also supported in AWS GLue.   

Since AWS Glue is a serverless service, users are not required to provision, configure and spin-up servers and they do not need to spend time managing servers.   

At the heart of AWS Glue is the Catalog, a centralized metadata repository for all data assets. In this repository, all relevant information about data assets (such as table definitions, data locations, file types, schema information) is stored.

In order to get this information into the Catalog AWS GLue uses crawlers. These crawlers can scan data stores and automatically infer the schema of any structured and semi-structured data that might be contained within the data stores.   
These crawlers can: 
* automatically discover datasets 
* discover file types 
* extract the schema
* store all this information in the Catalog. 

When data has been cataloged, it can then be accessed and ETL jobs can be performed on it. AWS Glue provides the capability to automatically generate ETL scripts, which can be used as a starting point, meaning users do not have start from scratch when developing ETL processes. In this blog however, we will be focussing on the use of an alternative to the AWS Glue ETL jobs. We will be making use of SQL queries implemented in AWS Athena to perform the ETL process.  

For the implementation and orchestration of more complex ETL processes, AWS Glue provides users with option of using workflows. These can be used to coordinate more complex ETL activities involving multiple crawlers, jobs and triggers. We will however be using an alternative to the these AWS Glue workflows, namely a state machine with step functions to coordinate our ETL process.  

To reiterate, AWS Glue has 3 main components:
* The Data Catalog, a centralized metadata repository, where all metadata information concerning  your data is stored. This includes information about tables (which define the metadata representations or schemas of the stored datasets), schemas and partitions. The metadata properties are inferred within data sources by crawlers, which also provide connections with them.
* The Apache Spark ETL engine. Once metadata is available in the data catalog and source and target data stores can be selected form the catalog, the Apache Spark ETL engine allows for the creation of ETL jobs that can be used to process the data.    
* The Scheduler. Users can set-up a schedule for their AWS ETL jobs. This schedule can be linked to a specific trigger (e.g. the completion of another ETL job), a particular time of day or a job can be set-up to run on-demand.

# Athena Service
As stated above, we used AWS Athena to run the ETL job, instead of a Glue ETL job with an auto generated script. 

The querying of datasets and data sources registered in the Glue Data Catalog is supported natively by AWS Athena. This means Athena will use the Glue Data Catalog as a cetralized location where it stores and retrieves table metadata. This metadata instructs the Athena query engine where it should read data, in what manner it should read the data and provides additional information required to process the data.
It is, for example, possible to run an INSERT INTO DML query against a source table registered with the Data Catalog. This query will insert rows into the destination table based upon a SELECT statement run against the source table.  
Directly below we show part of our complete INSERT INTO DML query, which has additional nested subqueries in which data from the source table is transformed step by step so that it can be repartitioned and used for analysis.   

> **INSERT INTO** "traffic"."sls_data_pipelines_batch_transformed"  
**SELECT** uniqueId, recordTimestamp, currentSpeed, bezettingsgraad, previousSpeed, CASE WHEN (avgSpeed3Minutes BETWEEN 0 AND 40) THEN 1 WHEN (avgSpeed3Minutes BETWEEN 41 AND 250) THEN 0 ELSE -1 END as trafficJamIndicator, CASE WHEN (avgSpeed20Minutes BETWEEN 0 AND 40) THEN 1 WHEN (avgSpeed20Minutes BETWEEN 41 AND 250) THEN 0 ELSE -1 END as trafficJamIndicatorLong, trafficIntensityClass2, trafficIntensityClass3, trafficIntensityClass4, trafficIntensityClass5, speedDiffindicator, avgSpeed3Minutes, avgSpeed20Minutes, year, month, day, hour   
**FROM**   
(**SELECT** uniqueId, recordTimestamp, currentSpeed, bezettingsgraad, previousSpeed, trafficIntensityClass2, trafficIntensityClass3, trafficIntensityClass4,         trafficIntensityClass5, CASE WHEN (currentSpeed - previousSpeed >= 20) THEN 1 WHEN (currentSpeed - previousSpeed <= -20) THEN -1 ELSE 0 END AS speedDiffindicator, avg(currentSpeed) OVER (PARTITION BY uniqueId ORDER BY originalTimestamp ROWS BETWEEN 2 PRECEDING AND 0 FOLLOWING) AS avgSpeed3Minutes, avg(currentSpeed) OVER (PARTITION BY uniqueId ORDER BY originalTimestamp ROWS BETWEEN 19 PRECEDING AND 0 FOLLOWING) AS avgSpeed20Minutes,year(originalTimestamp) as year, month(originalTimestamp) as month, day(originalTimestamp) as day, hour(originalTimestamp) as hour  
**FROM**  
(**SELECT**...

The (part of the) INSERT INTO DML query shown directly above, performed the following:
* Final selection of relevant information for data analysis. Not all information contained in the raw data was useful for analysis and some data was possibly invalid (e.g. due to malfunctioning measuring equipment)  
* The computation of aggregate values and derived fields to be used for analysis purposes (e.g. average speed over the last 3 minutes or the last 20 minutes, traffic jam indicators, etc..)  
* The repartitioning of the data by event time (i.e the year, month and day values of the originalTimestamp). Repartitioning is achieved by first defining a target table in the AWS Glue Catalog in which year, month, day and hour bigint fields were designated as Partition keys. Subsequently, we extracted the year, month and day values of the originalTimestamp (i.e. the timestamp of the measurement itself, not the timestamp of the processing time on Kinesis) and finally these values where assigned to the year, month, day and hour bigint fields which we designated as Partition keys in the target table. 

The additional nested subequeries, performed the following:
* The selection and transformation (where necesarry) of relevant information from the source data for the computation of aggregate values and derived fields   
* The selection of a subset of locations from the total amount of 4600 measurement locations and the natural regrouping of these locations (e.g. grouping of sets of lanes on the same road) 
* The splitting of queries into data ranges of (maximum) 4 days (i.e. a range between a start day and an end day). Because Amazon imposes a limit of 100 simultaneously written partitions using an INSERT INTO statement, we implemented a Lamda funtion to execute multiple concurrent queries. The splitting of the queries, limits the amount of simultaneously written partitions to 96 hours.     
 
For a link to the complete INSERT INTO DML query, please refer to https://github.com/becloudway/serverless-data-pipelines-batch-processing/blob/master/queries/InsertETL.sql.  
For a link to the explanation of field definitions please refer to https://github.com/becloudway/serverless-data-pipelines-batch-processing. 

When using AWS Athena to perform the ETL job, as opposed to using Glue ETL jobs, there is no functionality to automatically start the next process in a workflow. Therefore we also implemented a polling mechanism in order to periodically check for crawler/ETl query completion.

# Alternative solution for the ETL workflow
As already mentioned several times, we could also have used Glue ETL jobs for the implementation of the ETL workflow. These ETL jobs handle all processing and repartitioning of the data through python scripts with Spark.

In our next blog in the series we will explore the practical implementation of this alternative solution and compare the advantages and disadvantages of the use of Glue ETL jobs vs. AWS Athena ETL queries for the implementation of ETL workflows.   











