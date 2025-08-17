I have a docker-compose file below 

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
      - _AIRFLOW_WWW_USER_CREATE=True
      - _AIRFLOW_WWW_USER_USERNAME=admin
      - _AIRFLOW_WWW_USER_PASSWORD=admin
      - _AIRFLOW_WWW_USER_EMAIL=admin@example.com
      - _AIRFLOW_WWW_USER_FIRSTNAME=Admin
      - _AIRFLOW_WWW_USER_LASTNAME=User
    volumes:
      - ./dags:/opt/airflow/dags
      - airflow_db:/opt/airflow  # <-- shared volume

volumes:
  airflow_db:  # define the volume

I ran docker compose up -d --build.

Other commnds ran and results
$ docker ps
CONTAINER ID   IMAGE                             COMMAND                  CREATED          STATUS                        PORTS      NAMES
6c4afd68b989   apache/airflow:2.9.1-python3.10   "/usr/bin/dumb-init …"   15 minutes ago   Restarting (1) 1 second ago              airflow-webserver
aae63ed8fdf8   apache/airflow:2.9.1-python3.10   "/usr/bin/dumb-init …"   15 minutes ago   Up 5 seconds                  8080/tcp   airflow-scheduler

docker logs airflow-scheduler

ERROR: You need to initialize the database. Please run `airflow db init`. Make sure the command is run using Airflow version 2.9.1.
ERROR: You need to initialize the database. Please run `airflow db init`. Make sure the command is run using Airflow version 2.9.1.

ERROR: You need to initialize the database. Please run `airflow db init`. Make sure the command is run using Airflow version 2.9.1.
ERROR: You need to initialize the database. Please run `airflow db init`. Make sure the command is run using Airflow version 2.9.1.

ERROR: You need to initialize the database. Please run `airflow db init`. Make sure the command is run using Airflow version 2.9.1.
ERROR: You need to initialize the database. Please run `airflow db init`. Make sure th

What to do next to succeefully launch airflow ui in localhost

<br />
<br />

Got it 👍 — the error means your **Airflow metadata database hasn’t been initialized yet**.

Right now, both your **webserver** and **scheduler** are trying to start, but Airflow refuses to run until the DB schema is set up (`airflow db init`).

Here’s what you should do:

---

### ✅ Steps to fix and launch Airflow UI

1. **Initialize the Airflow DB once** (inside the container or via `docker compose run`):

   ```bash
   docker compose run airflow-webserver airflow db init
   ```

   This will create `airflow.db` inside your shared volume (`airflow_db`).

2. **(Optional) Create the admin user**
   Since you already passed `_AIRFLOW_WWW_USER_*` env vars, the user will be auto-created the first time the scheduler/webserver runs *after DB init*.
   But if you want to be sure, you can also manually run:

   ```bash
   docker compose run airflow-webserver airflow users create \
     --username admin \
     --firstname Admin \
     --lastname User \
     --role Admin \
     --email admin@example.com \
     --password admin
   ```

3. **Restart everything**
   After DB is initialized:

   ```bash
   docker compose down
   docker compose up -d
   ```

4. **Access UI**
   Go to [http://localhost:8080](http://localhost:8080) and log in with:

   * **Username:** `admin`
   * **Password:** `admin`

---

### ⚠️ Notes about your setup

* You’re using **SQLite** as the DB (`sqlite:////opt/airflow/airflow.db`), which is **not meant for multi-container setups**.

  * With `SequentialExecutor`, it’s fine for testing/demo, but **don’t use this in production**.
  * If you later switch to `CeleryExecutor` or `LocalExecutor`, you’ll need **Postgres or MySQL**.

* Your `airflow-webserver` is currently **restarting** because it can’t connect to the DB. Once you init the DB, it will stop crashing.

---

👉 Run step **1 (`airflow db init`)**, then restart, and you should be able to open the UI.

Do you want me to also rewrite your `docker-compose.yml` into a **minimal production-like setup with Postgres backend** (so you won’t hit SQLite limitations later)?
