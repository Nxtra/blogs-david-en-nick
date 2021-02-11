# Serverless data pipelines: ETL workfow with Step Functions and AWS Glue ETL jobs
This blog is Part 4 of a multi-part series around analysing Flanders’ traffic whilst leveraging the power of cloud components!

For part 1 see: [https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d](https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d)  
For part 2 see: [https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409](https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409)
For part 3 see :[https://https://medium.com/cloubis/serverless-data-pipelines-etl-workflow-with-step-functions-and-athena-83ca59b7bf35] (https://https://medium.com/cloubis/serverless-data-pipelines-etl-workflow-with-step-functions-and-athena-83ca59b7bf35)

# Korte Inleiding (wat zijn glue etl jobs, waarvoor gebruiken; etc…)
In this blog we aim to explore the use AWS Glue ETL jobs to repartition raw streaming data events and to contrast this approach to the solution with AWS Athena we implemented in our previous blog (link toevoegen aan blog woord of overbodig?).
To quickly reiterate, in our previous blog we used the AWS Glue service in conjunction with the AWS Athena service to repartition raw streaming data events we previously landed on an Amazon S3 bucket.
When these events landed on the S3 bucket, they were partitioned according to the Kinesis processing time and not according to event timestamps, the latter being the partitioning required for meaningful analysis. 

In AWS Glue jobs are scripts that contain the (business) logic based upon which AWS Glue will execute the extract, transform and load (ETL) steps to be performed on the source data   

