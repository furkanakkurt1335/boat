###########
# BUILDER #
###########

# pull official base image
FROM python:3.11.9-alpine as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev git

# lint
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pip install flake8==3.9.2
COPY . .
RUN flake8 --ignore=E501,F401 ./django_project

# copy Pipfile and Pipfile.lock first to leverage Docker cache
COPY Pipfile Pipfile.lock /usr/src/app/

# install dependencies
RUN pipenv install --system --deploy

#########
# FINAL #
#########

# pull official base image
FROM python:3.11.9-alpine

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup -S app && adduser -S app -G app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/mediafiles
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq
COPY --from=builder /usr/src/app/Pipfile /usr/src/app/Pipfile.lock $APP_HOME/
RUN pip install --no-cache-dir pipenv
RUN pipenv install --deploy --system

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.sh
RUN chmod +x  $APP_HOME/entrypoint.sh

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# run entrypoint.sh
ENTRYPOINT ["/home/app/web/entrypoint.sh"]
