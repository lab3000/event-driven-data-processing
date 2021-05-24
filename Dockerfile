FROM prefecthq/prefect:0.14.19-python3.8

RUN mkdir /app 

COPY /app /app
COPY pyproject.toml /app

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

RUN chmod +x ./connect_prefect.py
RUN poetry run ./connect_prefect.py