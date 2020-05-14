import shlex
import logging
from copy import deepcopy
from typing import List, Union


logger = logging.getLogger(__name__)


class MLBoxRunner(object):
    """Base class for all MLBox runners.

    TODO: Think about making `execute` method asynchronous on user request.
    """

    def __init__(self, config: dict):
        """  """
        self.__config = deepcopy(config)

    @property
    def config(self):
        return self.__config

    @staticmethod
    def format_command(cmd: Union[List[str], str]) -> List[str]:
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        if not isinstance(cmd, list):
            raise ValueError("The type(cmd) = {} which is not one of [list, str].".format(type(cmd)))
        return cmd

    def configure(self):
        """ Configure a (remote) platform.
        TODO: Do we want here to setup the remote environment, such as installing missing packages?
        """
        raise NotImplementedError()

    def execute(self, cmd: Union[List[str], str]) -> int:
        """ Execute command `cmd` on a platform specified by `platform_config`.
        Args:
            cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
                specific platform described by `platform_config`. Needs to be compatible with `subprocess.Popen` call.

        TODO: Do we need to capture output?
        """
        raise NotImplementedError()
