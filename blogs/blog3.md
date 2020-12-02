# Serverless data pipelines: ETL job with Athena

a.      Korte Introductie tot AWS Glue (wat zijn tables , catalog , crawler,…)

b.      State machine (Nick)
Doel: repartitioning the data so that it is partioned based on the timestamp in the events.
How: We are basically writing ETL here because we are going to extract the existing data from S3, transform it by creating new coloms based on the timestamp and land it in new partitions.

A couple of things need to happen:
* We need to figure out what the current data looks like. 
Ergo, register a schema in the GLUE catalog for our current data.
  * In order to find this schema we run a Crawler.
  The name says it all, a crawler will search his way trough the existing data, explore it and find out what the format is
  * A crawler finishes by creating a schema for the current data and registering that schema in Glue
* Next we need to run an ETL process to transform the data into new partitions.
In this blog we will use Athena for that
* When the data is repartitioned, we want to be able to query it.
Therefor, again, we need to know what the data looks like and thus we'll run a crawler.
This crawler will register the new  schema in Glue

It would not be effecient to do this process continuously.
Though, on the other hand we don't want to do this only once a week. 
Since then we'd have to wait a week to run the reporting on the data.

We have a process of a few managed steps (running crawler, registering schema, executing ETL job, running crawler) that we need to orchestrate on a regular basis.
Hence, it would be ideal for orchestration using AWS step functions.

*In AWS Step Functions you define your workflows in the Amazon States Language. 
The Step Functions console provides a graphical representation of that state machine to help visualize your application logic.
States are elements in your state machine. 
A state is referred to by its name, which can be any string, but which must be unique within the scope of the entire state machine*

Here is overview of what our state machine will look like:

![state-machine-steps-overview](img/../../img/blog3/statemachine.png)

As you see we have a finite number of steps each being executed one after the other.

### ASL - Amazon State Language

A state machine is defined using the `ASL` or Amazon States Language. 
This is a JSON base language to define the steps of your state machine.
We'll later look deeper into the logic executed in each step.
Let's first look at the ASL that defines these steps.

AWS Sam and the Serverless Framework both allow you to specify the ASL as `yaml`.
Using `yaml` improved readability we found.
As such we defined our `ASL` as follows. 
(Read below to find out more about what we are defining here)

```yaml
BatchProcessingStateMachine:
  events:
    - schedule: rate(1 day)
  name: BatchProcessingStateMachine
  definition:
    Comment: "State machine for the batch processing pipeline"
    StartAt: RunDataCrawler
    States:
      RunDataCrawler:
        Type: Task
        Resource: arn:aws:lambda:#{AWS::Region}:#{AWS::AccountId}:function:${self:service}-${opt:stage}-RunDataCrawler
        Next: WaitCrawler
      WaitCrawler:
        Type: Wait
        Seconds: 30
        Next: GetCrawlerState
      GetCrawlerState:
        Type: Task
        Resource: arn:aws:lambda:#{AWS::Region}:#{AWS::AccountId}:function:${self:service}-${opt:stage}-GetCrawlerState
        Next: CheckCrawlerState
      CheckCrawlerState:
        Type: Choice
        Default: WaitCrawler
        Choices:
          - And:
            - Variable: '$.CrawlerState'
              StringEquals: READY
            - Variable: '$.CrawlerStatus'
              StringEquals: SUCCEEDED
            Next: RunETLInsertAthena
          - And:
            - Variable: '$.CrawlerState'
              StringEquals: READY
            - Variable: '$.CrawlerStatus'
              StringEquals: FAILED
            Next: CrawlerFailed
      CrawlerFailed:
        Type: Fail
        Cause: "Crawler run has failed"
        Error: "Crawler run has failed"
      RunETLInsertAthena:
        Type: Task
        Resource: arn:aws:lambda:#{AWS::Region}:#{AWS::AccountId}:function:${self:service}-${opt:stage}-RunETLInsertAthena
        Next: WaitAthena
      WaitAthena:
        Type: Wait
        Seconds: 30
        Next: GetAthenaState
      GetAthenaState:
        Type: Task
        Resource: arn:aws:lambda:#{AWS::Region}:#{AWS::AccountId}:function:${self:service}-${opt:stage}-GetAthenaState
        Next: CheckAthenaState
      CheckAthenaState:
        Type: Choice
        Default: WaitAthena
        Choices:
          - Variable: '$.AthenaState'
            StringEquals: SUCCEEDED
            Next: SuccessEndState
          - Variable: '$.AthenaState'
            StringEquals: FAILED
            Next: AthenaFailed
      AthenaFailed:
        Type: Fail
        Cause: "Athena ETL insert query has failed"
        Error: "Athena ETL insert query has failed"
      SuccessEndState:
        Type: Succeed
```

This `ASL` describes the same workflow as the state image above. 
It's only much harder to read for human eyes.

Note that indeed we have the steps: running crawler, registering schema, executing ETL job, running crawler.
But we also have "wait" steps were we periodically check if a crawler is ready with his work.
And we have failure states that we use to react on failure in our process.

<!-- TODO: nog meer uitleg over wat er in elke ASL stap gedefinieerd wordt. Type, Resource, Choice Error, Next, Seconds .. -->

c.      Step functions (Nick)
Now it is time to look a little deeper into what happens every step.

**RunDataCrawler**
This triggers the executing of a Lambda Function which in turn triggers a Glue Crawler

```python
glue_client = boto3.client('glue')
CRAWLER_NAME = os.environ['CRAWLER_NAME']


def handle(event, context):
    timezone = pytz.timezone('Europe/Brussels')
    now = datetime.now(timezone)
    response = glue_client.start_crawler(Name=CRAWLER_NAME)
    return {'response': response, 'year': event.get('year', now.year), 'month': event.get('month', now.month), 'day': event.get('day', now.day-1)}
```

**GetCrawlerState**
We are periodically checking the state of the running crawler.
Since there is no direct integration for crawler events with step functions (yet?), we have to check this using a lambda function.

```python
glue_client = boto3.client('glue')
CRAWLER_NAME = os.environ['CRAWLER_NAME']


def handle(event, context):
    response = glue_client.get_crawler(Name=CRAWLER_NAME)['Crawler']
    return {'CrawlerState': response['State'], 'CrawlerStatus': response.get('LastCrawl', {'Status': None})['Status'],
            'year': event['year'], 'month': event['month'], 'day': event['day']}
```

This then tells us whether or not the crawler is finished.
And thus, wheter or not we can move on to the next step of our workflow

**RunETLInsertAthena**
When the crawler is finished it is time to run the ETL job.
This is done using AWS `Athena`. 
Read more about the how and what of `Athena` in the next paragraph.

It is however the job of a Lambda function to start the ETL job in `Athena` and to check when it is finished.

The handler of the lambda function that starts the ETL job looks as follows.
```python
def handle(event, context):
    try:
        queries = create_queries(event['year'], event['month'], event['day'])
    except Exception as e:
        return {'Response': 'FAILED', 'Error': str(e)}
    execution_ids = []
    for query in queries:
        try:
            response = execute_query(query)
            execution_ids.append(response)
        except Exception as e:
            return {'Response': 'FAILED', 'Error': str(e)}
    return {'Response': 'SUCCEEDED', 'QueryExecutionIds': execution_ids}

```
For more details on the methods being executed in the function check out the linked git repository.
Basically it comes down to this:
* define the queries, specifying which data range you want to repartition
* pass this queries to `Athena`
* return the Athena execution ID. An ID that we can use to check on the state of the ETL job with Athena.

The next function checks if the ETL job is finished.
It does so by using the execution ID that was returned from the latest step.

```python
def handle(event, context):
    response = athena_client.batch_get_query_execution(QueryExecutionIds=event['QueryExecutionIds'])
    for execution in response['QueryExecutions']:
        state = execution['Status']['State']
        if state != 'SUCCEEDED':
            return {'AthenaState': state, 'QueryExecutionId': execution['QueryExecutionId'], 'QueryExecutionIds': event['QueryExecutionIds']}
    for execution in response['UnprocessedQueryExecutionIds']:
        error = execution.get('ErrorMessage', None)
        if error is not None:
            return {'AthenaState': 'FAILED', 'QueryExecutionId': execution['QueryExecutionId'], 'Error': error}
    return {'AthenaState': 'SUCCEEDED'}
```
<!-- todo: meer uitleg bij bovenstaande -->

We now saw the steps necessary in the workflow to repartition our data.
This repartitioning happens with Athena. 
Let's dive deeper into that in the next paragraph.

d.      Athena service (hoe query lezen?, etc..)

e.      Alternatieve oplossing (Glue Etl job -- pyspark; kort vermelden kan aparte blog zijn)
