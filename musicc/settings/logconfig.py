# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
import os
import logging.config
import logging.handlers
import logging


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(filename)s %(funcName)s %(lineno)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(asctime)s %(message)s"},
        "musicc_format": {
            "format": "Level: %(levelname)s, Time: %(asctime)s, Module: %(module)s, Process: %(process)d, Thread: %(thread)d, File: %(filename)s, Function: %(funcName)s, Line: %(lineno)d, Message: %(message)s"
        },
        "musicc_json_format": {
            "format": '{"Level": "%(levelname)s", "Time": "%(asctime)s", "Module": "%(module)s", "Process": "%(process)d", "Thread": "%(thread)d", "File": "%(filename)s", "Function": "%(funcName)s", "Line": "%(lineno)d", "Message": "%(message)s"}'
        },
    },
    "handlers": {
        "musicc_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/debug.log",
            "formatter": "musicc_json_format",
        },
        "musicc_db_log": {
            "level": "DEBUG",
            "class": "django_db_logger.db_log_handler.DatabaseLogHandler",
            "formatter": "musicc_json_format",
        },
        "musicc_console": {
            "level": "INFO",
            "formatter": "musicc_format",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
    },
    "loggers": {
        "musicc": {
            "handlers": ["musicc_console", "musicc_db_log", "musicc_file"],
            "level": "DEBUG",
            "propagate": True,
        }
    },
}
