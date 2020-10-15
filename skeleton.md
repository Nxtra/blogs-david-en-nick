# Serverless data transform with kinesis

![architecture](./img/architecture.png)

## What are we trying to do here (David)

- land raw events on s3
- create a data lake on s3 to query on
- create a data lake in a queryable format
- think about access pattern and partitioning

## Landing data on s3 with Kinesis Firehose

### Kinesis data streams vs Kinesis firehose (Nick)

- mooi vergelijkende afbeelding

## Transform and land the data

### converting / transforming the data format (David)

From json to parquet

- Why?
  - Better queryable
  - Less storage neede

### Partitioning using firehose (Nick)

What is and isn't possible

-> Hive style partitioning and the advantages
`myPrefix/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/`

[https://docs.aws.amazon.com/athena/latest/ug/partition-projection-kinesis-firehose-example.html](https://docs.aws.amazon.com/athena/latest/ug/partition-projection-kinesis-firehose-example.html)
[https://aws.amazon.com/blogs/big-data/amazon-kinesis-data-firehose-custom-prefixes-for-amazon-s3-objects/](https://aws.amazon.com/blogs/big-data/amazon-kinesis-data-firehose-custom-prefixes-for-amazon-s3-objects/)

# Cloudformation example?

# Conclusion (Nick + David)

We have created a datalake on s3 that is partitioned, queryable and in optimal format.
