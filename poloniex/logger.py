import inspect
import logging

import pp

__author__ = 'andrew.shvv@gmail.com'


class PoloniexLogger(logging.Logger):
    def get_prev_method_name(self):
        return inspect.stack()[2][3]

    def info(self, msg, *args, **kwargs):
        pretty_msg = pp.fmt(msg)
        additional_description = "Func:  %s\n" % self.get_prev_method_name()
        super().info(additional_description + pretty_msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        pretty_msg = pp.fmt(msg)
        additional_description = "Func: %s\n" % self.get_prev_method_name()
        super().warning(additional_description + pretty_msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        pretty_msg = pp.fmt(msg)
        additional_description = "Func: %s\n" % self.get_prev_method_name()
        super().debug(additional_description + pretty_msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        pretty_msg = pp.fmt(msg)
        additional_description = "Func: %s\n" % self.get_prev_method_name()
        super().exception(additional_description + pretty_msg, *args, **kwargs)


class LogMixin(object):
    def __init__(self):
        super().__init__()
        # override the class
        logging.setLoggerClass(PoloniexLogger)

        # create logger
        name = '.'.join([__name__, self.__class__.__name__])
        self.logger = logging.getLogger(name)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('Level: %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(ch)
