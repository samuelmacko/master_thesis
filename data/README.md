# Gathering of a dataset for master thesis

## Running in a container

### Build

Example:

```
docker build -f Dockerfile.search_repos . -t thesis_app:latest
```

### Run

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

## Running in an OpenShift cluster

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
