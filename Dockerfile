FROM prefecthq/prefect:0.14.19-python3.8

RUN mkdir /app 

COPY /app /app
COPY pyproject.toml /app
COPY poetry.lock /app

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry==1.1.6
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT python ./connect_prefect.py