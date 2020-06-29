# master thesis (name?)

Thesis is divided into two parts. The task of the first part is to compile a dataset. In the second part, model will be trained and evaluated.

## Data gathering

Data gathering is also divided into two phases.

Preferred way of running the code is as a container. Solution for persistent storage for all the generated files in this phase is [Amazon S3](https://aws.amazon.com/s3/).

### First phase - collecting and sorting IDs

Program will crawl public [Github](https://github.com/) repositories and evaluate their type as either __maintained__, __unmaintained__, or __not suitable__ for the purposes of the thesis. IDs will be saved into _.dat_ files.

Repositories will be crawled until the _end condition_ is met. End condition says how many IDs of what type we want.

### Second phase - computing features

Computation of features.

### Configuration

User is expected to configure data gathering part through [configuration file](configs/gathering.yml). Description of settings:

| Setting | Description |
| ------- | ----------- |
| end_condition | End condition type, see [here](data_gathering/enums.py) |
| end_value | End condition value (e.g. 100) |
| from_year | Repositories created before this year will not be considered for the evaluation |
| to_year | Repositories created after this year will not be considered for the evaluation |
| maintained_ids | Path to file where IDs of maintained repositories will be stored |
| unmaintained_ids | Path to file where IDs of unmaintained repositories will be stored |
| not_suitable_ids | Path to file where IDs of not suitable repositories will be stored |
| maintained_csv_file | Path to .csv file where computed features of maintained repositories will be stored |
| unmaintained_csv_file | Path to .csv file where computed features of unmaintained repositories will be stored |
| features_file | Path to .yaml file with list of features to compute |
| s3_region | name of the region for [S3](https://aws.amazon.com/s3/) bucket |

### Running in a container

#### Build

Example:

```
docker build -f Dockerfile.search_repos . -t thesis_app:latest
```

#### Run

Container expects these environmental variables.

| Name | Description |
| ---- | ----------- |
| AWS_ACCESS_KEY_ID | [AWS](https://aws.amazon.com/) access key |
| AWS_SECRET_ACCESS_KEY | [AWS](https://aws.amazon.com/) secret access key |
| BUCKET_NAME | name of the [S3](https://aws.amazon.com/s3/) bucket |
| ENDPOINT_URL | URL of [S3](https://aws.amazon.com/s3/) endpoint |
| GITHUB_ACCESS_TOKEN | [Github API](https://developer.github.com/v3/) access token to authenticate the user |

Example:

```
docker run -e GITHUB_ACCESS_TOKEN -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e ENDPOINT_URL -e BUCKET_NAME -t thesis_app:latest
```

or

```
docker run --env-file ./env_file -t thesis_app:latest
```

### Running in an OpenShift cluster

First, log in into your OpenShift cluster:

```
oc login <cluster>
```

Next, select project in which the application should run:

```
oc project <my-project-name>
```

And finally, process the OpenShift template that will create a build config,
image stream and a job. The build config will build the image from the current master branch:

```
oc process -f openshift.yaml -p GITHUB_ACCESS_TOKEN=<token> -p AWS_ACCESS_KEY_ID=<key-id> -p AWS_SECRET_ACCESS_KEY=<access-key> | oc apply -f -
```

To clean up objects created:

```
oc delete bc,is,job -l app=samuelmacko-master-thesis
```
