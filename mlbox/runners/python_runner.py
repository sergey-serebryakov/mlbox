import logging
import os
import shutil
from typing import Union, List
from mlbox import metadata
from mlbox.util import Utils
from mlbox.runners.mlbox_runner import MLBoxRunner
logger = logging.getLogger(__name__)


class PythonRunner(MLBoxRunner):

    def __init__(self, mlbox: metadata.MLBox, platform_config: dict):
        # TODO: refactor and fix this
        super(PythonRunner, self).__init__({})
        self.mlbox = mlbox
        if self.mlbox.implementation_type != 'python':
            raise ValueError("Incorrect implementation type ({})".format(self.mlbox.implementation_type))
        if not isinstance(self.mlbox.implementation, metadata.PythonImplementation):
            raise ValueError("Incorrect metadata ({})".format(type(self.mlbox.implementation)))

    def configure_python(self, python: str, requirements: Union[None, str]):
        if requirements in (None, ''):
            logger.info("PythonRunner [configure] no python requirements found, configuration done.")
            return
        cmd = "{} -m pip install".format(python)
        if requirements.endswith(".txt"):
            cmd = "{} -r {}".format(cmd, os.path.join(self.mlbox.path, requirements))
        else:
            cmd = "{} {}".format(cmd, requirements)
        logger.info("Installing packages with pip: {}".format(cmd))
        Utils.run_or_die(cmd)
        logger.info("PythonRunner [configure] python requirements installed, configuration done.")

    def configure_conda(self):
        impl: metadata.PythonImplementation = self.mlbox.implementation
        conda: dict = impl.conda
        # TODO: do not create if exists
        # Create Python environment
        cmd = '{} create --name {} python={} --no-default-packages --yes'.format(conda['conda'], conda['name'],
                                                                                 conda['version'])
        Utils.run_or_die(cmd)

        # Install packages
        cmd = '{} install --name {} --yes'.format(conda['conda'], conda['name'])
        if impl.requirements.endswith(".txt"):
            cmd = "{} --file {}".format(cmd, os.path.join(self.mlbox.path, impl.requirements))
        else:
            cmd = "{} {}".format(cmd, impl.requirements)
        logger.info("Installing packages with pip: {}".format(cmd))
        Utils.run_or_die(cmd)

    def configure_virtualenv(self):
        impl: metadata.PythonImplementation = self.mlbox.implementation
        virtualenv: dict = impl.virtualenv
        # Check if python environment exists
        virtualenv_path = os.path.join(self.mlbox.path, virtualenv['location'])
        if os.path.exists(virtualenv_path):
            if impl.force_reconfigure is False:
                return
            shutil.rmtree(virtualenv_path)
        # Create it
        cmd = "virtualenv -p {} {}".format(virtualenv['base_interpreter'], virtualenv_path)
        logger.info(cmd)
        Utils.run_or_die(cmd)
        # Initialize it
        self.configure_python(os.path.join(virtualenv_path, 'bin', 'python'), impl.requirements)

    def configure(self):
        impl: metadata.PythonImplementation = self.mlbox.implementation
        if impl.interpreter == 'system':
            # No need to check for python, just confirm packages installed.
            self.configure_python(impl.system['interpreter'], impl.requirements)
        elif impl.interpreter == 'conda':
            self.configure_conda()
        elif impl.interpreter == 'virtualenv':
            self.configure_virtualenv()
        else:
            raise NotImplemented("Not implemented yet")

    def get_python_path(self):
        impl: metadata.PythonImplementation = self.mlbox.implementation
        if impl.interpreter == 'system':
            return impl.system['interpreter']
        if impl.interpreter == 'conda':
            conda_base = os.path.dirname(os.path.dirname(impl.conda['conda']))
            return os.path.join(conda_base, 'envs/{}/python.exe'.format(impl.conda['name']))
        if impl.interpreter == 'virtualenv':
            return os.path.join(
                os.path.join(self.mlbox.path, impl.virtualenv['location']),
                'bin',
                'python'
            )
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
        Utils.run_or_die(cmd)
        return 0
