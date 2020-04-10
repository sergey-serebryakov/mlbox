import logging
import os
from typing import Union, List
from mlbox import mlbox_metadata
from mlbox.mlbox_local_run import run_or_die
from mlbox.runners.lib.runner import MLBoxRunner
logger = logging.getLogger(__name__)


class PythonRunner(MLBoxRunner):

    def __init__(self, mlbox: mlbox_metadata.MLBox):
        # TODO: refactor and fix this
        super(PythonRunner, self).__init__({})
        self.mlbox = mlbox
        if self.mlbox.implementation_type != 'python':
            raise ValueError("Incorrect implementation type ({})".format(self.mlbox.implementation_type))
        if not isinstance(self.mlbox.implementation, mlbox_metadata.PythonImplementation):
            raise ValueError("Incorrect metadata ({})".format(type(self.mlbox.implementation)))

    def configure_python(self, python: str, requirements: str):
        if requirements in (None, ''):
            return
        cmd = "{} -m pip install".format(python)
        if requirements.endswith(".txt"):
            cmd = "{} -r {}".format(cmd, os.path.join(self.mlbox.path, requirements))
        else:
            cmd = "{} {}".format(cmd, requirements)
        logger.info("Installing packages with pip: {}".format(cmd))
        run_or_die(cmd)

    def configure_conda(self):
        impl: mlbox_metadata.PythonImplementation = self.mlbox.implementation
        conda: dict = impl.conda
        # TODO: do not create if exists
        # Create Python environment
        cmd = '{} create --name {} python={} --no-default-packages --yes'.format(conda['conda'], conda['name'],
                                                                                 conda['version'])
        run_or_die(cmd)

        # Install packages
        cmd = '{} install --name {} --yes'.format(conda['conda'], conda['name'])
        if impl.requirements.endswith(".txt"):
            cmd = "{} --file {}".format(cmd, os.path.join(self.mlbox.path, impl.requirements))
        else:
            cmd = "{} {}".format(cmd, impl.requirements)
        logger.info("Installing packages with pip: {}".format(cmd))
        run_or_die(cmd)

    def configure(self):
        impl: mlbox_metadata.PythonImplementation = self.mlbox.implementation
        if impl.interpreter == 'system':
            # No need to check for python, just confirm packages installed.
            self.configure_python(impl.system['interpreter'], impl.requirements)
            return
        elif impl.interpreter == 'conda':
            self.configure_conda()
            return
        raise NotImplemented("Not implemented yet")

    def get_python_path(self):
        impl: mlbox_metadata.PythonImplementation = self.mlbox.implementation
        if impl.interpreter == 'system':
            return impl.system['interpreter']
        if impl.interpreter == 'conda':
            conda_base = os.path.dirname(os.path.dirname(impl.conda['conda']))
            return os.path.join(conda_base, 'envs/{}/python.exe'.format(impl.conda['name']))
        raise NotImplemented("Not implemented yet")

    def execute(self, cmd: Union[List[str], str]) -> int:
        # C:\projects\anaconda3\Scripts\conda.exe
        # C:\projects\anaconda3\envs\mnist_python
        # TODO: ad-hoc implementation, fix me
        python = self.get_python_path()
        entrypoint = os.path.join(self.mlbox.path, self.mlbox.implementation.entrypoint)
        cmd = "{} {} --mlbox_task {}".format(python, entrypoint, self.mlbox.implementation.task['name'])
        for param, value in self.mlbox.implementation.task['input_params'].items():
            cmd = "{} --{}={}".format(cmd, param, value)
        logger.info("MLBox executable: %s", cmd)
        run_or_die(cmd)
        return 0
