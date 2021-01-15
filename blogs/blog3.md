# Serverless data pipelines: ETL workfow with Step Functions and Athena
This blog is Part 3 of a multi-part series around analysing Flanders’ traffic whilst leveraging the power of cloud components!    
For part 1 see: https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d  
For part 2 see: https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409  

# What is the goal we are trying to achieve?
The goal of this blog to explore the use of the AWS Glue service in conjunction with the AWS Athena service in order to repartition raw streaming data events. We previously landed these events on an Amazon S3 bucket partitioned according to the processing time on Kinesis. Now, however, we would like to have these events partitioned according to event timestamps to allow for meaningful batch analysis.    

# First as short introduction to AWS Glue (wat zijn tables , catalog , crawler,…)
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

> I**NSERT INTO** "traffic"."sls_data_pipelines_batch_transformed"  
**SELECT** uniqueId, recordTimestamp, currentSpeed, bezettingsgraad, previousSpeed, CASE WHEN (avgSpeed3Minutes BETWEEN 0 AND 40) THEN 1 WHEN (avgSpeed3Minutes BETWEEN 41 AND 250) THEN 0 ELSE -1 END as trafficJamIndicator, CASE WHEN (avgSpeed20Minutes BETWEEN 0 AND 40) THEN 1 WHEN (avgSpeed20Minutes BETWEEN 41 AND 250) THEN 0 ELSE -1 END as trafficJamIndicatorLong, trafficIntensityClass2, trafficIntensityClass3, trafficIntensityClass4, trafficIntensityClass5, speedDiffindicator, avgSpeed3Minutes, avgSpeed20Minutes, year, month, day, hour   
**FROM** (**SELECT** ...)

The INSERT INTO query performed the following:
* Selection of relevant information. Not all information contained in the raw data was useful for analysis and some data was possibly invalid (due to malfunctioning measuring equipment)
* A natural grouping of locations (i.e. by sets of lanes on the same road). Additionally a selection of certain points of interest within each location (i.e. certain lanes were selected within each grouping)
* The computation of aggregate values and derived fields to be used for analysis purposes (e.g. average speed over the last 3 minutes or the last 20 minutes, traffic jam indicators, etc..)  
* The repartitioning of the data by event time (year, month, day). Repartitioning was achieved by first defining a  target table in the AWS Glue Catalog in which year, month, day and hour bigint fields were designated as Partition keys. Subsequently, in the INSERT INTO query we first converted the time of measurement to a Unix time (which we called originalTimestamp), then we grouped all data according to their location and originalTimestamp values and finally we extracted year, month, day and hour Partition key values for each grouping   
As Amazon imposes a limit of 100 simultaneously written partitions using an INSERT INTO statement, we implemented a Lamda funtion to execute multiple concurrent queries. For this purpose queries were split into date ranges of (maximum) 4 days (i.e. a range between a start day and an end day), which limites the amount of simultaneously written partitions to 96 hours.
> WHERE year(originalTimestamp)={year} AND month(originalTimestamp)={month} AND day(originalTimestamp) BETWEEN {start_day} AND {end_day}

For a link to the complete ETL Athena query please refer to https://github.com/becloudway/serverless-data-pipelines-batch-processing/blob/master/queries/InsertETL.sql.
For a link to the explanation of field definintions please refer to https://github.com/becloudway/serverless-data-pipelines-batch-processing. 



When using AWS Athena to perform the ETL job, as opposed to using Glue ETL jobs ,there is no functionality to automatically start the next process in a workflow. Therefore we also implemented a polling mechanism in order to periodically check for crawler/ETl query completion.

# Alternative solution for the ETL workflow
As already mentioned several times, we could also have used Glue ETL jobs for the implementation of the ETL workflow. These ETL jos handle all processing and repartitioning of the data through python scripts with Spark.

In our next blog in the series we will explore the practical implementation of this alternative solution and compare the advantages and disadvantages of the use of Glue ETL jobs vs. AWS Athena ETL queries for the implementation of ETL workflows.    










