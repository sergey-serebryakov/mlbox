import os
import logging
from copy import deepcopy
from typing import Union, List
from mlbox import metadata
from mlbox.util import Utils
from mlbox.runners.mlbox_runner import MLBoxRunner
logger = logging.getLogger(__name__)


class ExecRunner(MLBoxRunner):
    def __init__(self, mlbox: metadata.MLBox, platform_config: dict):
        # TODO: refactor and fix this
        super(ExecRunner, self).__init__({})
        self.mlbox = mlbox
        if self.mlbox.implementation_type != 'exec':
            raise ValueError("Incorrect implementation type ({})".format(self.mlbox.implementation_type))
        if not isinstance(self.mlbox.implementation, metadata.ExecImplementation):
            raise ValueError("Incorrect metadata ({})".format(type(self.mlbox.implementation)))

    def configure(self):
        current_work_dir = os.getcwd()
        os.chdir(self.mlbox.path)

        impl: metadata.ExecImplementation = self.mlbox.implementation
        for directory in impl.directories:
            os.makedirs(os.path.join(self.mlbox.path, directory), exist_ok=True)
        for cmd in impl.configure:
            logger.info("Running configure step: {}".format(cmd))
            Utils.run_or_die(cmd)

        os.chdir(current_work_dir)

    def execute(self, cmd: Union[List[str], str]) -> int:
        current_work_dir = os.getcwd()
        os.chdir(self.mlbox.path)
        # The `self.mlbox.implementation.task['input_params']` is a dictionary of input parameters, such as,
        # parameters_file, data_dir, log_dir etc.
        env_vars: dict = {}
        input_params = self.mlbox.implementation.task['input_params']
        for param in input_params:
            if param == 'parameters_file':
                env_vars.update(Utils.load_yaml(input_params[param]))
            else:
                env_vars.update({param: input_params[param]})
        #
        impl: metadata.ExecImplementation = self.mlbox.implementation
        for cmd in impl.run:
            cmd: str = deepcopy(cmd)
            for name, value in env_vars.items():
                cmd = cmd.replace('${' + name + '}', str(value))
                cmd = cmd.replace('$' + name, str(value))
            logger.info("Running run step: {}".format(cmd))
            Utils.run_or_die(cmd)
        #
        os.chdir(current_work_dir)
        return 0
