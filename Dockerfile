FROM python:3.13.8-slim

RUN apt-get update && apt-get install -y iputils-ping gdal-bin aptitude libpq-dev libgdal-dev libsqlite3-mod-spatialite gcc g++

# Install Poetry
RUN export MSGPACK_PUREPYTHON=1 && pip3 install poetry

# RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal && export C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Copy only the dependency files first
COPY pyproject.toml poetry.lock /app/

# Install dependencies

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . /app

ENV SPATIALITE_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/mod_spatialite

# Expose the application port (FastAPI default is 8000)
EXPOSE 8000

CMD ["uvicorn", "main:app","--host", "0.0.0.0", "--port", "80"]