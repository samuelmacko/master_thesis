FROM python:3.8

MAINTAINER Samuel Macko "samuel.macko.sm@gmail.com"

ENV PROJECT_DIR=/tmp/thesis_app \
    VOLUME_DIR=/tmp/thesis_data

VOLUME ${VOlUME_DIR}

WORKDIR ${PROJECT_DIR}

COPY . ${PROJECT_DIR}/

RUN pip install pipenv && \
    pipenv install --system --deploy

ENTRYPOINT [ "python", "main.py", "--search-repos" ]
