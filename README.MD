# LLMOps

An LLM application development and operation platform based on LangGraph and Flask.

## How to start

### Install Python Dependencies:

1. Before installing the Python dependencies, we recommend you create a virtual environment:

    ```bash
    python -m venv venv
    ```

2. Install Python packages with pip

    ```bash
    pip install -r requirements.txt
    ```

### Create Environment File `.env`

Create the environment file `.env` on the project root path with the following configurations for setting the
environment
variables, which are used in the project:

```dotenv
# Flask-WTF配置
WTF_CSRF_ENABLED=False

# SQLAlchemy数据库配置
SQLALCHEMY_DATABASE_URI=postgresql://postgres:19981018@127.0.0.1:5432/llmops?client_encoding=utf8
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_ECHO=True

# OpenAI配置
OPENAI_API_KEY={your_openai_api_key}
OPENAI_BASE_URL={your_openai_base_url}
```

> 1. Adjust the database information in the `SQLALCHEMY_DATABASE_URI` as you need.
> 2. Input the `OPENAI_API_KEY` and `OPENAI_BASE_URL`, which you can get from the OpenAI Platform (charging for tokens).

### Run Database

We use PostgreSQL as an example; you can choose other databases like MySQL as you need.

1. Pull PostgreSQL docker image:

    ```bash
    docker pull postgres
    ```

2. Run docker container by the script `scripts/postgres-dev-docker-run.sh` (change the `POSTGRES_USER` and
   `POSTGRES_PASSWORD` in the script as you need):

    ```bash
    sh scripts/postgres-dev-docker-run.sh
    ```

### Create Database Tables

You can create database tables with [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/).

1. Init Flask DB:

    ```bash
    flask --app app.http.app db init
    ```

2. Create migration script:

    ```bash
    flask --app app.http.app db migrate -m "create_table"
    ```

3. Upgrade database (tables will be created):

    ```bash
    flask --app app.http.app db upgrade
    ```

## How to Test

We use [pytest](https://docs.pytest.org/en/stable/) as our test framework.
You can configure the pytest configuration in the `pytest.ini` file.
The test codes are under the `test` folder.

Run test with `pytest`:

```bash
pytest
```
