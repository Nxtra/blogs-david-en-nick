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

# Athena Service
As stated above, we used AWS Athena to run the ETL job. 

The querying of datasets and data sources registered in the Glue Data Catalog is supported natively by AWS Athena. This means Athena will use the Glue Data Catalog as a cetralized location where it stores and retrieves table metadata. This metadata instructs the Athena query engine where it should read data, in what manner it should read the data and provides additional information required to process the data.
It is, for example, possible to run an INSERT INTO DML query against a source table registered with the Data Catalog. This query will insert rows into the destination table based upon a SELECT statement run against the source table. 

The INSERT INTO query (see directly below), which we used to run the ETL job, performed the following:
* The computation of aggregate values and derived fields (to be used for analysis purposes)
* Selection of relevant information (not all information contained in the raw data was usefull for analysis)
* A natural grouping of locations (e.g. by a set of lanes on the same road)
* The repartitioning of the data by event time (year, month, day)

> INSERT INTO "anpr"."sls_data_pipelines_batch_transformed"
SELECT uniqueId, recordTimestamp, currentSpeed, bezettingsgraad, previousSpeed,
CASE WHEN (avgSpeed3Minutes BETWEEN 0 AND 40) THEN 1
WHEN (avgSpeed3Minutes BETWEEN 41 AND 250) THEN 0
ELSE -1 END as trafficJamIndicator,
CASE WHEN (avgSpeed20Minutes BETWEEN 0 AND 40) THEN 1
WHEN (avgSpeed20Minutes BETWEEN 41 AND 250) THEN 0
ELSE -1 END as trafficJamIndicatorLong,
trafficIntensityClass2, trafficIntensityClass3, trafficIntensityClass4, trafficIntensityClass5,
speedDiffindicator, avgSpeed3Minutes, avgSpeed20Minutes, year, month, day, hour
FROM
(
SELECT uniqueId, recordTimestamp, currentSpeed, bezettingsgraad, previousSpeed,
trafficIntensityClass2, trafficIntensityClass3, trafficIntensityClass4, trafficIntensityClass5,
CASE
WHEN (currentSpeed - previousSpeed >= 20) THEN 1
WHEN (currentSpeed - previousSpeed <= -20) THEN -1
ELSE 0 END AS speedDiffindicator,
avg(currentSpeed) OVER (PARTITION BY uniqueId ORDER BY originalTimestamp ROWS BETWEEN 2 PRECEDING AND 0 FOLLOWING) AS avgSpeed3Minutes,
avg(currentSpeed) OVER (PARTITION BY uniqueId ORDER BY originalTimestamp ROWS BETWEEN 19 PRECEDING AND 0 FOLLOWING) AS avgSpeed20Minutes,
year(originalTimestamp) as year, month(originalTimestamp) as month, day(originalTimestamp) as day, hour(originalTimestamp) as hour FROM
(
SELECT uniqueId, recordTimestamp, originalTimestamp, currentSpeed, bezettingsgraad, trafficIntensityClass2,
trafficIntensityClass3, trafficIntensityClass4, trafficIntensityClass5,
lag(currentSpeed, 1) OVER (PARTITION BY uniqueId ORDER BY originalTimestamp) as previousSpeed FROM
(
SELECT MAX(uniqueId) as uniqueId, lve_nr, originalTimestamp, recordTimestamp, AVG(currentSpeed) as currentSpeed,
TRY(CAST(SUM(trafficIntensityClass2) AS INTEGER)) as trafficIntensityClass2,
TRY(CAST(SUM(trafficIntensityClass3) AS INTEGER)) as trafficIntensityClass3,
TRY(CAST(SUM(trafficIntensityClass4) AS INTEGER)) as trafficIntensityClass4,
TRY(CAST(SUM(trafficIntensityClass5) AS INTEGER)) as trafficIntensityClass5,
TRY(CAST(ROUND(AVG(bezettingsgraad)) AS INTEGER)) as bezettingsgraad FROM
(
SELECT lve_nr,
unieke_id as uniqueId,
from_unixtime(CAST(tijd_waarneming as INTEGER)) as originalTimestamp,
tijd_waarneming as recordTimestamp,
CASE WHEN verkeersintensiteit_klasse2 + verkeersintensiteit_klasse3 + verkeersintensiteit_klasse4 + verkeersintensiteit_klasse5 > 0 THEN
(voertuigsnelheid_rekenkundig_klasse2 + voertuigsnelheid_rekenkundig_klasse3 + voertuigsnelheid_rekenkundig_klasse4 + voertuigsnelheid_rekenkundig_klasse5)/
(CASE WHEN verkeersintensiteit_klasse2 > 0 THEN 1 ELSE 0 END +
CASE WHEN verkeersintensiteit_klasse3 > 0 THEN 1 ELSE 0 END +
CASE WHEN verkeersintensiteit_klasse4 > 0 THEN 1 ELSE 0 END +
CASE WHEN verkeersintensiteit_klasse5 > 0 THEN 1 ELSE 0 END)
END
as currentSpeed,
verkeersintensiteit_klasse2 as trafficIntensityClass2,
verkeersintensiteit_klasse3 as trafficIntensityClass3,
verkeersintensiteit_klasse4 as trafficIntensityClass4,
verkeersintensiteit_klasse5 as trafficIntensityClass5,
verkeersintensiteit_klasse2 + verkeersintensiteit_klasse3 + verkeersintensiteit_klasse4 + verkeersintensiteit_klasse5 as bezettingsgraad FROM
"anpr"."sls_data_pipelines_batch_destination_parquet"
WHERE rekendata_bezettingsgraad > -1 AND defect=0)
WHERE year(originalTimestamp)={year} AND month(originalTimestamp)={month} AND day(originalTimestamp) BETWEEN {start_day} AND {end_day}
AND uniqueId IN (32, 37, 1840, 2125, 3388, 3391, 753, 1065, 3159, 2161, 216, 217, 1132)
GROUP BY lve_nr, originalTimestamp, recordTimestamp
)
)
)



