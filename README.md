# master thesis

Short description

## Running in as a container

### Build

```
docker build . -t thesis_app:latest
```

### Run

Container expects an enviromental variable `GITHUB_ACCESS_TOKEN` which contains a valid Github API token.
This token will be used to authenticate the user.

```
docker run -e GITHUB_ACCESS_TOKEN -t thesis_app:latest
```