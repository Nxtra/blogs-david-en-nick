# Serverless data pipelines: ETL workfow with Step Functions and Athena
Algemene inleiding (link naar vorige blogs + algemeen doel van deze blog beschrijven, enz..) -> TO DO

a.    Korte Introductie tot AWS Glue (wat zijn tables , catalog , crawler,…)
	
 AWS Glue is a serverless Extract, Transform and Load (ETL) cloud-optimized service.
The service has three main attributes:
1. It is serverless. This means there is no need to for users to provision, configure and spin-up servers and therefore there is also no life cycle management of the servers.
2. It provides crawlers. These crawlers allow for automatic schema inference of structured and semi-structured data. These crawlers can: 
	* automatically discover datasets 
	* discover file types 
	* extract the schema
	* store all this information in a centralized metadata repository, which in AWS Glue is called the Catalog. The information stored in the catalog can then be used for querying and analysis      
3. The automated scripts
