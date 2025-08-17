You're still seeing:

```
ERROR: You need to initialize the database. Please run `airflow db init`.
```

That means **the metadata DB was not initialized** — or it's not being shared properly between the `webserver` and `scheduler`.

---

## 🔍 Root Cause

You're using **SQLite**, which stores the database in a local file:

```
/opt/airflow/airflow.db
```

Each service (`airflow-webserver`, `airflow-scheduler`) **must use the same volume**, or they will each create their **own separate database**, which leads to errors like this.

---

## ✅ Fix in 3 Steps

### 🔧 Step 1: Add a **named volume** to `docker-compose.yml`

Update your file to include a shared volume that all services can use:

```yaml

services:
  airflow-webserver:
    image: apache/airflow:2.9.1-python3.10
    container_name: airflow-webserver
    restart: always
    command: webserver
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=SequentialExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./dags:/opt/airflow/dags
      - airflow_db:/opt/airflow  # <-- shared volume
    depends_on:
      - airflow-scheduler

  airflow-scheduler:
    image: apache/airflow:2.9.1-python3.10
    container_name: airflow-scheduler
    restart: always
    command: scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=SequentialExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./dags:/opt/airflow/dags
      - airflow_db:/opt/airflow  # <-- shared volume

volumes:
  airflow_db:  # define the volume
```

This makes sure **all containers share the same airflow\.db file**.

---

### 🔧 Step 2: Clean up and reinitialize

Now remove the orphaned/leftover containers and volumes:

```bash
docker compose down -v --remove-orphans
```

Then initialize the DB again:

```bash
docker compose run --rm airflow-webserver airflow db migrate
```

And create the user:

```bash
docker compose run --rm airflow-webserver airflow users create \
  --username airflow \
  --password airflow \
  --firstname Air \
  --lastname Flow \
  --role Admin \
  --email airflow@example.com
```

---

### 🚀 Step 3: Start Airflow

```bash
docker compose run airflow airflow db init
docker compose up -d
```

Then open:

```
http://localhost:8080
```

Login with: `airflow` / `airflow`

---

<br />

## Restart the airflow server when already created images

> docker compose down -v --remove-orphans

> docker compose run --rm airflow-webserver airflow db migrate

> docker compose up -d