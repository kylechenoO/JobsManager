"""
Task Sample Execution Module

This module provides a sample entry point for interacting with
the task scheduling subsystem. It demonstrates how to initialize
runtime dependencies and perform basic task and job operations.

Responsibilities:
- Load configuration
- Initialize logging
- Establish database connection
- Attach database-backed logging
- Create and manage scheduled jobs via Task abstraction
"""

## version related
__author__ = "Kyle"
__version__ = "0.0.1"
__email__ = "kyle@hacking-linux.com"

## import build in pkgs
import re
import os
import sys
import json
import argparse

## Resolve project root directory 
workpath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

## Extend Python module search path for project libraries
sys.path.append("%s/lib" % (workpath))

## import private pkgs
from Log import Log
from MySQL import MySQL
from Config import Config
from Task import Task
from Job import Job

class TaskSample(object):
    """
    Task scheduling sample controller.

    This class bootstraps the required runtime environment
    and demonstrates how to manage scheduled jobs using
    the Task and Job abstractions.

    Lifecycle:
        1. Load configuration
        2. Initialize logging
        3. Establish database connection
        4. Execute task scheduling operations
    """

    def __init__(self) -> None:
        """
        Initialize the task sample runtime.

        This includes:
        - Loading configuration
        - Injecting runtime metadata
        - Initializing the logger
        - Connecting to the database
        - Attaching MySQL-backed logging
        """

        ## set private values
        self.config = Config(workpath).config
        self.config['pid'] = os.getpid()
        self.config['pname'] = os.path.basename(__file__)
        self.config['name'] = re.sub(r'\..*$', '', self.config['pname'])

        ## logger init
        self.loggerObj = Log(self.config)
        self.logger = self.loggerObj.logger

        ## debug prt
        self.logger.debug({'db.host': self.config['db']['host']})
        self.logger.debug({'db.port': self.config['db']['port']})
        self.logger.debug({'db.username': self.config['db']['username']})
        self.logger.debug({'db.password': self.config['db']['password']})
        self.logger.debug({'db.database': self.config['db']['database']})
        self.logger.debug({'db.charset': self.config['db']['charset']})

        ## init MySQLObj
        self.MySQLObj = MySQL(self.logger, self.config['db']['host'], self.config['db']['port'], self.config['db']['username'], self.config['db']['password'], self.config['db']['database'], self.config['db']['charset'])
        self.MySQLObj.connect()

        ## prt log to mysql
        self.loggerObj.add_mysql_handler(self.MySQLObj, self.config['log']['table'])
        self.logger.debug({'status': 'start'})

        ## debug output
        self.logger.debug({'status': 'end'})

    def __destory__(self) -> None:
        """
        Release allocated resources.

        This method disconnects the database connection.
        Intended to be called during shutdown.
        """

        self.MySQLObj.disconnect()

    def run(self) -> bool:
        """
        Execute task scheduling operations.

        This method initializes a Task instance using configuration
        values and demonstrates common job operations such as
        listing, adding, updating, and removing jobs.

        Returns:
            bool: True if execution completes successfully
        """

        taskObj = Task(self.logger,
                      self.config['db']['host'],
                      self.config['db']['port'],
                      self.config['db']['username'],
                      self.config['db']['password'],
                      self.config['db']['database'],
                      self.config['db']['charset'],
                      self.config['jobsmanager']['table'],
                      self.config['jobsmanager']['timezone'],
                      self.config['jobsmanager']['coalesce'],
                      self.config['jobsmanager']['max_instances'],
                      )

        """
        ## job operation samples
        ## add job
        job = Job(
            id="job_echo",
            command='echo "[$(date +%Y-%m-%d\\ %H:%M:%S)] hello world" | tee -a /tmp/run.log',
            second="*",
        )
        taskObj.add_job(job = job, replace_existing = True)

        ## list jobs
        taskObj.list_jobs()

        ## get specify job info
        taskObj.get_job('job_echo3')

        ## remove job
        taskObj.remove_job('job_echo')

        ## modify job
        job = Job(
            id="job_echo3",
            command='echo "[$(date +%Y-%m-%d\\ %H:%M:%S)] hello world 3 start" | tee -a /tmp/run3.log; sleep 10; echo "[$(date +%Y-%m-%d\\ %H:%M:%S)] hello world 3 end" | tee -a /tmp/run3.log',
            second="*",
            timeout=2
        )
        taskObj.update_job(job = job)
        """

        self.logger.debug({'status': 'start'})

        ## list jobs
        taskObj.list_jobs()

        self.logger.debug({'status': 'end'})
        return True

def main() -> None:
    """
    Application entry point.

    Initializes the TaskSample instance and executes
    task scheduling operations.
    """

    taskSampleObj = TaskSample()
    taskSampleObj.run()

if __name__ == "__main__":
    """
    Command-line entry point.

    This function is executed only when the module is run as a
    script. It will not be executed when the module is imported.
    """

    main()

