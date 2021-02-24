# Serverless data pipelines: ETL workfow with Step Functions and AWS Glue ETL jobs
This blog is Part 4 of a multi-part series around analysing Flanders’ traffic whilst leveraging the power of cloud components!

For part 1 see: [https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d](https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d)  
For part 2 see: [https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409](https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409)   
For part 3 see :[https://medium.com/cloubis/serverless-data-pipelines-etl-workflow-with-step-functions-and-athena-83ca59b7bf35](https://https://medium.com/cloubis/serverless-data-pipelines-etl-workflow-with-step-functions-and-athena-83ca59b7bf35)

# Korte Inleiding (wat zijn glue etl jobs, waarvoor gebruiken; etc…)
In this blog we aim to explore the use AWS Glue ETL jobs to repartition raw streaming data events and to contrast this approach to an alternative solution, repartitioning the raw streaming data events with AWS Athena, we implemented in our previous blog.

To quickly reiterate, when our raw streaning data events are first landed on an Amazon S3 bucket, they are partitioned according to the Kinesis processing time and not according to event timestamps, the latter of course being the partitioning required for any meaningful analysis. An additional goal is to improve the queryability of the raw data. This includes computation of aggregate values (e.g. average speeds, traffic jam indicators), adding a natural grouping of events (e.g. by sets of lanes on the same road) and of course filtering out the relevant data.        

In order to achieve the above, several approaches can be viable. One such an approach is the use of *jobs* in the AWS Glue service.  
These *jobs* are basically scripts that allow you to connect to source data, perform ETL on that data and finally store the resulting transformed data in a location of your choosing. In other words, these scripts usually contain the (business) logic based upon which AWS Glue will execute the extract, transform and load (ETL) steps to be performed on the source data. AWS Glue can generate these scripts on its own, which can be used as a starting point and then, if needed, further adjusted to the particular needs of the situation.

In general there are three distinct types of *jobs*:
 * **Spark Jobs**, these process data in batches and are run in an Apache Spark environment that is managed by the AWS Glue service.
 * **Streaming ETL Jobs**, these allow the performance of ETL transformations on data streams and are run in the Apache Spark Streaming framework.
 * **Python shell jobs**, these run Python scripts as a shell and can be used to schedule and execute tasks for which an Apache Spark environment is not needed.  
In this blog we will be implementing a **Spark job**.  

?? Job properties bespreken??

The AWS Glue service also provides the capability of creating *triggers*, which can start *jobs* based on a particular schedule, a certain condition (e.g. the successful completion of another *job*) or on-demand. ??onnodig om dit toe te voegen??

# Vergelijking Glue ETL job met Athena aanpak (vanuit technisch oogpunt)



 

