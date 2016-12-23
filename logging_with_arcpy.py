# -*- coding: utf-8 -*-
"""
This module allows Python's logging module and Esri's ArcMap tools to play nicely together.

Everything here works with the root logger, there is currently no functionality to work with multiple loggers.

The standard logging.basicConfig() doesn't work out of the box in ArcMap tools, because the logging session lives
throughout the ArcMap session, and isn't restarted with every tool invocation. init_logging() can be used instead of
basicConfig(), and takes care of this issue by performing the necessary (re)initialisations.

Furthermore, flush_and_close_logger() should be called at the end of each script, to ensure that all output is flushed
when the script terminates. For the same reason mentioned above, some logging output may be delayed otherwise.

Finally, the ArcPyLogHandler class (mostly adopted from
http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages) allows the logging module to send output to
ArcMap's tool output window, using arcpy.AddMessage(), etc.

TODO:
- ArcPyLogHandler currently creates an empty file as given in input. If it isn't used, it shouldn't be created.

Created by: Hanne L. Petersen <halpe@sdfe.dk>
Created on: 2016-08-26
"""

import os
import socket
import logging
import logging.handlers

import arcpy

def init_logging(filename="log.txt", level=logging.INFO, fmt="", datefmt='%d-%m-%Y %H:%M', mode='a'):
    """
    Initialise a useful logging session. For ArcMap tools, logging.basicConfig probably won't do what you want... (details below)

    Use fmt="%(asctime)s %(message)s" to log without user and computer name.

    If filename is a relative path, it will be relative to C:\Windows\System32 for tools called from an ArcMap toolbox.
    So just use absolute paths...

    Note that if you're using the logging module from inside ArcMap, e.g. from a tool in a toolbox, your logging session
    will survive within the ArcMap session! In addition, the logging.basicConfig() function is intended to be run only
    once ("only the first call will actually do anything: subsequent calls are effectively no-ops", from
    https://docs.python.org/2/howto/logging.html#logging-advanced-tutorial)
    I.e., you may have two tools that write to different log files - this won't work if you run both tools from the same
    ArcMap session, and you do it the naive way.
    Or if you run a tool several times inside the same ArcMap session, calling basicConfig WILL DO NOTHING. I.e.
    debugging sucks big time.

    In ArcMap you probably want to run flush_and_close_logger() at the end of your script, otherwise output can
    sometimes be delayed.

    Other format placeholders can be found in https://docs.python.org/2/library/logging.html#logrecord-attributes

    TODO: The proper way for this module might be something with inheritance or subclassing...
    """
    # Some useful snippets for copy-pasting when debugging:
    # import logging
    # root_logger = logging.getLogger()
    # h = root_logger.handlers[0]
    # root_logger.removeHandler(h)
    # print([h.baseFilename for h in root_logger.handlers])

    if fmt == '':
        # Default format prepend user name and computer name.
        # http://stackoverflow.com/questions/799767/getting-name-of-windows-computer-running-python-script?answertab=active#tab-top
        fmt = "%(asctime)s {} {} %(message)s".format(os.getenv('USERNAME'), socket.gethostname().upper())

    root_logger = logging.getLogger()

    # Need to run regular basicConfig first - seems like it does something we need...
    # Whatever logging level is set to a restrictive level here, it will persist throughout (looks like a bug).
    # If it's set to a low level here (or NOTSET), it seems to work fine, respecting what's set later.
    # The filename is replaced properly later.
    logging.basicConfig(level=logging.NOTSET)

    # Start by removing all existing handlers from the root logger
    # Remove from the back, to avoid the indexes going haywire
    for i in range(len(root_logger.handlers)-1, -1, -1):
        root_logger.removeHandler(root_logger.handlers[i])

    # Then set up the new handler with appropriate formatter
    # https://docs.python.org/2/library/logging.handlers.html#logging.FileHandler
    add_handler(logging.FileHandler(filename, mode=mode, encoding=None, delay=False), level=level)


def add_handler(h, level=logging.INFO, fmt="", datefmt='%d-%m-%Y %H:%M'):
    """Add a handler."""
    root_logger = logging.getLogger()

    if fmt == '':
        fmt = "%(asctime)s {} {} %(message)s".format(os.getenv('USERNAME'), socket.gethostname().upper())

    # Prep the Formatter, and add it
    # https://docs.python.org/2/library/logging.html#logging.Formatter
    f = logging.Formatter(fmt, datefmt)

    # Add the level and formatter to the handler
    # https://docs.python.org/2/library/logging.handlers.html#logging.FileHandler
    # https://docs.python.org/2/library/logging.html#handler-objects
    h.setLevel(level)
    h.setFormatter(f)
    root_logger.addHandler(h)


def flush_and_close_logger():
    """From ArcMap there seem to be some problems with flushing, and this seems to help..."""
    for h in logging.getLogger().handlers:
        h.flush()
    logging.shutdown()


def _logging_is_active():
    """Check if a logging session has been initiated (e.g. with logging.basicConfig())."""
    # http://stackoverflow.com/questions/26017073/how-to-get-filename-from-a-python-logger
    return len(logging.getLogger().handlers) > 0


class ArcPyLogHandler(logging.handlers.RotatingFileHandler):
    """
    Custom logging class that passes messages to the arcpy tool window.

    From http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages
    """

    # TODO: This class is still initting a RotatingFileHandler for the init filename and creating a file
    #  - this file should be removed (or the init re-implemented)

    def emit(self, record):
        """Write the log message."""
        # It shouldn't be necessary to reimport, but it seems to be, otherwise it can crash, when several tools are
        # run inside the same ArcMap session...
        # Perhaps the imports from the first run get cleared, but because the logging session somehow survives, they
        # don't get imported again?
        import logging
        import arcpy

        try:
            my_msg = self.format(record)  # fixed this - the code at stackexchange didn't work for me here
            # msg = record.msg.format(record.args)  # old code
        except:
            my_msg = record.msg

        if record.levelno >= logging.ERROR:
            arcpy.AddError(my_msg)
        elif record.levelno >= logging.WARNING:
            arcpy.AddWarning(my_msg)
        else:  # everything else goes here (if you don't want debug, remove it from the handler, if you do want it,
               #  there's nowhere else to send it to
            arcpy.AddMessage(my_msg)

        # The following line would send the message to the regular RotatingFileHandler, but we don't want that here:
        # super(ArcPyLogHandler, self).emit(record)

# end class ArcPyLogHandler
