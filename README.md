# JobsManager

**Author:** Kyle

**Email:** [kyle@hacking-linux.com](mailto:kyle@hacking-linux.com)

**Version:** 0.0.1

## Overview

JobsManager is a lightweight, database-driven job scheduling service built on top of **APScheduler** and **MySQL**.

It is designed as a long-running service and focuses on:

* Persistent job scheduling
* Explicit, database-controlled reloads
* Clear separation between job management and scheduler runtime
* Predictable behavior suitable for production environments

## Architecture Overview

```
┌─────────────────────┐
│ bin/JobsManager.py  │
│ Service entry point │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ JobsManagerService  │
│ Scheduler runtime   │
│ - APScheduler       │
│ - reload logic      │
│ - signal handling   │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ Task                │
│ Job management API  │
│ - add / update      │
│ - remove / list     │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ Job                 │
│ Job definition      │
│ - cron schedule     │
│ - shell command     │
└─────────────────────┘
```

## Directory Structure

```
JobsManager/
├── bin/
│   ├── JobsManager.py
│   └── TaskSample.py
├── etc/
│   └── global.json
├── lib/
│   ├── Config.py
│   ├── Job.py
│   ├── JobsManagerService.py
│   ├── Log.py
│   ├── MySQL.py
│   └── Task.py
├── log/
│   └── jobsmanager.log
├── systemd/
│   └── jobsmanager.service
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Core Components

### JobsManagerService

`lib/JobsManagerService.py`

The scheduler runtime service responsible for:

* Initializing APScheduler with a MySQL-backed job store
* Managing scheduler lifecycle (start / stop)
* Detecting database changes
* Reloading scheduler state safely
* Handling graceful shutdown via system signals

### Task

`lib/Task.py`

A lightweight wrapper around APScheduler providing job management APIs:

* Add, update, remove scheduled jobs
* Translate `Job` definitions into cron triggers
* Execute shell commands with timeout control

### Job

`lib/Job.py`

A pure data model describing a scheduled job:

* Job identifier
* Shell command
* Cron-style schedule fields
* Execution timeout

## Scheduler Reload and Database Coordination

JobsManager uses MySQL as the single source of truth for job persistence and scheduler reload coordination.

Reloads are explicit, rate-limited, and controlled by database state.

### Runtime & Reload Flow

```
┌───────────────────────────┐
│ JobsManager.py            │
│ Service entry point       │
└──────────────┬────────────┘
               │
┌──────────────▼────────────┐
│ JobsManagerService        │
│ runtime loop              │
│ - poll DB                 │
│ - reload if needed        │
└──────────────┬────────────┘
               │
        check  │
               │
┌──────────────▼────────────┐
│ jm_update_info            │
│ reload marker table       │
│ - updated = 0 ?           │
└──────────────┬────────────┘
               │
     full      │
     reload    │
               │
┌──────────────▼────────────┐
│ APScheduler               │
│ SQLAlchemyJobStore        │
│ - load jobs from MySQL    │
└───────────────────────────┘
```

### Reload Control Logic

* Job changes do not directly reload the scheduler
* A marker row is inserted into `jm_update_info` with `updated = 0`
* The scheduler polls for pending markers
* Reload is triggered only when pending markers exist
* Reloads are serialized using a lock
* Scheduler state is rebuilt from database state

## Logging and Observability

JobsManager supports file-based and database-backed logging.

```
┌───────────────────────────┐
│ Application / Scheduler   │
│ - lifecycle events        │
│ - reload operations       │
│ - job execution           │
└──────────────┬────────────┘
               │
┌──────────────▼────────────┐
│ Logging subsystem         │
│ - file handler            │
│ - MySQL handler           │
└──────────────┬────────────┘
               │
┌──────────────▼────────────┐
│ jm_syslog                 │
│ persistent logs           │
└───────────────────────────┘
```

## Database Schema

This section describes the logical schema (ER-style) of JobsManager tables. DDL definitions are intentionally omitted from this README.

### jm_syslog

```
┌──────────────────────────────┐
│ jm_syslog                    │
├──────────────────────────────┤
│ id               (PK)        │
│ created_at                   │
│ level                        │
│ logger_name                  │
│ message                      │
├──────────────────────────────┤
│ Purpose:                     │
│ - Persistent system logging  │
│ - Reload and runtime logs    │
│ - Execution error logs       │
└──────────────────────────────┘
```

### jm_update_info

```
┌──────────────────────────────┐
│ jm_update_info               │
├──────────────────────────────┤
│ id               (PK)        │
│ updated                      │
│ insert_time                  │
│ update_time                  │
│ jobs_before_update           │
│ jobs_after_update            │
├──────────────────────────────┤
│ Purpose:                     │
│ - Signal scheduler reloads   │
│ - Track change context       │
└──────────────────────────────┘
```

### Table Interaction Summary

```
┌───────────────────────────┐
│ Job / Task Management     │
│ - add / update / remove   │
└──────────────┬────────────┘
               │
        insert │  updated = 0
               │
┌──────────────▼────────────┐
│ jm_update_info            │
│ reload marker             │
└──────────────┬────────────┘
               │
        poll   │
               │
┌──────────────▼────────────┐
│ JobsManagerService        │
│ - detect updates          │
│ - trigger reload          │
└──────────────┬────────────┘
               │
       log     │
               │
┌──────────────▼────────────┐
│ jm_syslog                 │
│ persistent logs           │
└───────────────────────────┘
```

## Job Definition and Parameters

Jobs are defined using the `Job` data model.

### Signature

```python
Job(
    id: str,
    command: str,
    second: str = "*",
    minute: str = "*",
    hour: str = "*",
    day: str = "*",
    month: str = "*",
    day_of_week: str = "*",
    timeout: int = 60
)
```

### Required Parameters

* `id`: Unique job identifier
* `command`: Shell command executed using `subprocess.run(..., shell=True)`

### Optional Parameters

* `second`, `minute`, `hour`, `day`, `month`, `day_of_week`: Cron-style schedule fields (default `"*"`)
* `timeout`: Max execution time in seconds (default `60`)

### Example

```python
job = Job(
    id="job_echo",
    command='echo "hello world"',
    minute="*/5",
    timeout=10
)
```

## Running JobsManager

### Manual Start

```bash
python bin/JobsManager.py
```

### systemd Deployment

```bash
cp systemd/jobsmanager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable jobsmanager
systemctl start jobsmanager
```

## Managing Jobs

`bin/TaskSample.py` demonstrates job operations such as list/add/update/remove.

## Design Principles

* Database is the source of truth
* Reloads are explicit and controlled
* Scheduler state is always rebuildable
* Observability is a first-class concern
* Designed for long-running supervised services

## License

MIT License

