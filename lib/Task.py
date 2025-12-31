"""
Task Scheduling Module

This module provides a lightweight task scheduling abstraction
built on top of APScheduler. It is responsible for managing
job definitions, scheduling execution, and invoking shell
commands based on cron-style triggers.

Responsibilities:
- Initialize a scheduler backed by a database job store
- Execute shell commands as scheduled jobs
- Provide basic job management operations
"""

## version related
__author__ = "Kyle"
__version__ = "0.0.1"
__email__ = "kyle@hacking-linux.com"

## import builtin pkgs
import subprocess
from urllib.parse import quote_plus
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

## import private pkgs
from Job import Job

class Task(object):
    """
    Task scheduler controller.

    This class wraps an APScheduler instance and exposes
    basic operations for managing scheduled jobs, including
    adding, updating, removing, and listing jobs.
    """

    def __init__(self, logger: object, host: str, port: int, username: str, password: str, database: str, charset: str, table: str, timezone: str, coalesce: str, max_instances: int) -> None:
        """
        Initialize the task scheduler.

        This includes:
        - Storing database connection parameters
        - Initializing scheduler configuration
        - Creating and starting the scheduler instance

        Args:
            logger (object): Application logger
            host (str): Database host
            port (int): Database port
            username (str): Database username
            password (str): Database password
            database (str): Database name
            charset (str): Database charset
            table (str): Job store table name
            timezone (str): Scheduler timezone
            coalesce (str): Job coalescing behavior
            max_instances (int): Maximum concurrent job instances

        Returns:
            None
        """

        ## application logger
        self.logger = logger
        self.logger.info({'status': 'start'})

        ## database connection parameters
        self.db_host = host
        self.db_port = port
        self.db_username = username
        self.db_password = quote_plus(password)
        self.db_database = database
        self.db_charset = charset

        ## scheduler configuration
        self.table = table
        self.coalesce = bool(coalesce)
        self.timezone = timezone
        self.max_instances = max_instances

        ## initialize scheduler
        self.init()
        self.logger.info({'status': 'end'})

    def init(self) -> None:
        """
        Initialize and start the APScheduler instance.

        This method creates a BackgroundScheduler with a
        SQLAlchemy-backed job store and starts it immediately.

        Returns:
            None
        """

        ## construct SQLAlchemy database URL
        db_url = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=%s' % (self.db_username, self.db_password, self.db_host, self.db_port, self.db_database, self.db_charset)
        self.logger.info({'db_url': db_url})

        ## create scheduler with MySQL job store
        self._scheduler = BackgroundScheduler(
            jobstores = {
                "default": SQLAlchemyJobStore(
                    url = db_url,
                    tablename = self.table,
                )
            },
            timezone = self.timezone
        )

        ## start scheduler immediately
        self._scheduler.start(paused = False)

    @staticmethod
    def run_command(logger: object, cmd: str, timeout: int) -> None:
        """
        Execute a shell command.

        This method is used as the scheduled job entry point.
        It executes the given shell command with an optional
        timeout and logs execution results.

        Args:
            logger (object): Application logger
            cmd (str): Shell command to execute
            timeout (int): Execution timeout in seconds

        Returns:
            None
        """
        logger.info({'status': 'start'})
        logger.info({'cmd': cmd})

        try:
            ## suppress output when redirecting to /dev/null
            if cmd.endswith('&> /dev/null'):
                cmd = cmd.removesuffix('&> /dev/null').strip()

                ## run cmd
                subprocess.run(
                    cmd,
                    shell = True,
                    stdout = subprocess.DEVNULL,
                    stderr = subprocess.DEVNULL,
                    timeout = timeout
                )
    
            else:
                ## run cmd
                subprocess.run(cmd, shell = True, timeout = timeout)

        except subprocess.TimeoutExpired as e:
            ## handle command execution timeout
            logger.error({'status': 'timeout: %s' % (str(e))})

        except Exception as e:
            ## handle unexpected execution errors
            logger.error({'status': 'timeout: %s' % (str(e))})

        logger.info({'status': 'end'})

    def shutdown(self) -> None:
        """
        Shutdown the scheduler.

        This method stops the scheduler without waiting
        for running jobs to complete.

        Returns:
            None
        """

        self.logger.info({'status': 'start'})
        self._scheduler.shutdown(wait = False)
        self.logger.info({'status': 'end'})

    def list_jobs(self) -> list:
        """
        List all scheduled jobs.

        This method retrieves all jobs from the scheduler
        and logs their key attributes.

        Returns:
            list: List of scheduled job objects
        """

        self.logger.info({'status': 'start'})
        ## retrieve all jobs from scheduler
        jobs = self._scheduler.get_jobs()

        ## log job details
        for job in jobs:
            self.logger.info({
                "id": job.id,
                "name": job.name,
                "func": f"{job.func.__module__}.{job.func.__qualname__}",
                "args": job.args,
                "kwargs": job.kwargs,
                "trigger": str(job.trigger),
                "next_run_time": (
                    job.next_run_time.isoformat()
                    if job.next_run_time else None
                ),
                "coalesce": job.coalesce,
                "max_instances": job.max_instances,
                "misfire_grace_time": job.misfire_grace_time,
                "executor": job.executor,
                "pending": job.pending,
            })

        self.logger.info({'status': 'end'})
        return jobs

    def get_job(self, job_id: str) -> Job:
        """
        Retrieve a scheduled job by ID.

        Args:
            job_id (str): Job identifier

        Returns:
            object: Job instance if found, otherwise None
        """

        self.logger.info({'status': 'start'})
        ## fetch job from scheduler
        job = self._scheduler.get_job(job_id)
        self.logger.info({'job': job})
        self.logger.info({'status': 'end'})
        return job

    def add_job(self, job: Job, replace_existing: bool = False) -> None:
        """
        Add a new scheduled job.

        This method converts a Job definition into a
        cron trigger and registers it with the scheduler.

        Args:
            job (Job): Job definition
            replace_existing (bool): Whether to replace an existing job

        Returns:
            None
        """

        self.logger.info({'status': 'start'})

        ## build cron trigger from job definition
        trigger = CronTrigger(
            second = job.second,
            minute = job.minute,
            hour = job.hour,
            day = job.day,
            month = job.month,
            day_of_week = job.day_of_week,
        )
    
        ## register job with scheduler
        self._scheduler.add_job(
            func = Task.run_command,
            trigger = trigger,
            args = [self.logger, job.command, job.timeout],
            id = job.id,
            name = job.command,
            replace_existing = replace_existing,
            coalesce = self.coalesce,
            max_instances = self.max_instances,
        )

        self.logger.info({'status': 'end'})

    def update_job(self, job: Job) -> None:
        """
        Update an existing scheduled job.

        This method replaces an existing job with a new
        definition. An error is raised if the job does not exist.

        Args:
            job (Job): Updated job definition

        Returns:
            None
        """

        self.logger.info({'status': 'start'})

        ## ensure job exists before update
        if not self._scheduler.get_job(job.id):
            raise JobLookupError(job.id)

        ## replace existing job definition
        self.add_job(job, replace_existing = True)

        self.logger.info({'status': 'end'})

    def remove_job(self, job_id: str) -> None:
        """
        Remove a scheduled job.

        Args:
            job_id (str): Job identifier

        Returns:
            None
        """

        self.logger.info({'status': 'start'})

        ## remove job from scheduler
        self._scheduler.remove_job(job_id)

        self.logger.info({'status': 'end'})

