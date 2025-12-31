"""
Job Definition Module

This module defines the Job data structure used by the task
scheduling system. A Job represents a single scheduled execution
unit, including its execution command and cron-style schedule
definition.
"""

## import builtin pkgs
from dataclasses import dataclass

@dataclass
class Job(object):
    """
    Scheduled job definition.

    This class represents a single schedulable job entry.
    It encapsulates the execution command along with
    cron-like scheduling fields and execution constraints.

    Attributes:
        id (str):
            Unique identifier of the job.

        command (str):
            Shell command to be executed when the job is triggered.

        second (str):
            Cron-style second field. Defaults to "*".

        minute (str):
            Cron-style minute field. Defaults to "*".

        hour (str):
            Cron-style hour field. Defaults to "*".

        day (str):
            Cron-style day-of-month field. Defaults to "*".

        month (str):
            Cron-style month field. Defaults to "*".

        day_of_week (str):
            Cron-style day-of-week field. Defaults to "*".

        timeout (int):
            Maximum execution time in seconds before the job
            is considered timed out.
    """

    id: str
    command: str
    second: str = '*'
    minute: str = '*'
    hour: str = '*'
    day: str = '*'
    month: str = '*'
    day_of_week: str = '*'
    timeout: int = 60
