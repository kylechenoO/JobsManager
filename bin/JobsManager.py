"""
Jobs Manager Service Entry Point

This module provides the main entry point for initializing and running
the Jobs Manager service. It is responsible for:

- Loading configuration
- Initializing logging
- Establishing database connections
- Attaching database-backed logging
- Starting the JobsManagerService runtime
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
from JobsManagerService import JobsManagerService

class JobsManager(object):
    """
    Core Jobs Manager controller.

    This class is responsible for bootstrapping all required subsystems
    needed by the Jobs Manager service, including configuration,
    logging, and database connectivity.

    Lifecycle:
        1. Load configuration
        2. Initialize logging
        3. Establish database connection
        4. Attach database-backed logging
        5. Start JobsManagerService
    """

    def __init__(self) -> None:
        """
        Initialize the Jobs Manager runtime environment.

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
        Intended to be called during service shutdown.
        """

        self.logger.debug({'status': 'start'})
        self.MySQLObj.disconnect()
        self.logger.debug({'status': 'end'})

    def run(self) -> bool:
        """
        Start the Jobs Manager service.

        This method initializes the JobsManagerService using
        configuration values and starts it in blocking mode.

        Returns:
            bool: True if the service is started successfully
        """

        self.logger.debug({'status': 'start'})

        ## gen service object
        scsvcObj = JobsManagerService(self.logger,
                                      self.config['db']['host'],
                                      self.config['db']['port'],
                                      self.config['db']['username'],
                                      self.config['db']['password'],
                                      self.config['db']['database'],
                                      self.config['db']['charset'],
                                      self.config['jobsmanager']['table'],
                                      self.config['jobsmanager']['timezone'],
                                      self.config['jobsmanager']['coalesce'],
                                      self.config['jobsmanager']['max_workers'],
                                      self.config['jobsmanager']['max_instances'],
                                      self.config['jobsmanager']['misfire_grace_time'],
                                      self.config['jobsmanager']['reload_interval']
                                      )
        ## run on background
        scsvcObj.serve_forever()

        self.logger.debug({'status': 'end'})
        return True

def main() -> None:
    """
    Application entry point.

    Initializes the JobsManager instance and starts
    the Jobs Manager service.
    """

    jbmObj = JobsManager()
    jbmObj.run()

if __name__ == "__main__":
    """
    Command-line entry point.

    This function is executed only when the module is run as a
    script. It will not be executed when the module is imported.
    """

    main()

