# Serverless data pipelines: ETL workfow with Step Functions and Athena
Algemene inleiding (link naar vorige blogs + algemeen doel van deze blog beschrijven, enz..) -> TO DO
Part 3  of a multi-part series around analysing Flanders’ traffic whilst leveraging the power of cloud components!
For part 1 see: https://medium.com/cloudway/real-time-data-processing-with-kinesis-data-analytics-ad52ad338c6d
For part 2 see: https://medium.com/cloubis/serverless-data-transform-with-kinesis-e468abd33409

# What is the goal we are trying to achieve?
The goal of this blog to explore the use of the AWS Glue service in conjunction with the AWS Athena service, to repartition the raw streaming data events we landed on an Amazon S3 bucket according to events timestamps (as opposed to the processing time on Kinesis).   

# Short introduction to AWS Glue (wat zijn tables , catalog , crawler,…)

AWS Glue is a serverless Extract, Transform and Load (ETL) cloud-optimized service, that can be used for the automated organization, location, movement and transformation of data sets stored within data lakes in Amazon Simple Storage Service (S3), data warehouses in Amazon Redshift and other databases that are part of the Amazon Relational Database Service. MySQL, Oracle, Microsoft SQL Server and PostgreSQL databases are also supported.   

Because Glue is serverless, there is no need to for users to provision, configure and spin-up servers and therefore there is also no life cycle management of the 		   servers.

Glue uses crawlers to scan data stores and automatically infer the schema of structured and semi-structured data. These crawlers can: 
	* automatically discover datasets 
	* discover file types 
	* extract the schema
	* store all this information in a centralized metadata repository, which in AWS Glue is called the Catalog. 

The information stored in the Data catalog can then be used for querying and analysis of data sets. After data is cataloged, it can be accessed and it is ready for ETL jobs. AWS Glue can automatically generate ETL scripts (which can be used as a starting point so users do not have start from scratch). In this blog however we will be making use of an alternative to the ETL jobs, which is making use of SQL queries implemented in AWS Athena. 

To reiterate, AWS Glue has 3 main components:
	* The Data Catalog. A centralized metadata repository, where information about tables (which define the metadata representations or schemas of the stored 		   	    datasets),schemas and partitions is stored. Crawlers infer the metadata properties within data sources and provide connections with them.
	* The ETL engine. Which allows for the creation of ETL jobs once metadata is available in the data catalog (and source and target data stores can be selected form the 	   	   catalog). AWS Glue makes use of Apavhe Spark as the underlying engine to process data records.
	* The Scheduler. Once an ETL job has been created, a schedule can be set-up for the job to be run. This can be on-demand, according to a particular trigger (e.g. the 		  completion of another ETL job) or at a certain time.

#
