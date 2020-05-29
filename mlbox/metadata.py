import sys
import os
from typing import Union


class MLBox:
    def __init__(self, path: str, tasks: Union[dict, None] = None):
        self.name = None
        self.path = os.path.abspath(path)
        self.tasks = {} if tasks is None else tasks
        self.implementation_type = None
        self.implementation = None

    def set_name(self, name: str):
        self.name = name

    def get_task(self, name) -> dict:
        return self.tasks[name]

    @property
    def readme_file(self) -> str:
        return os.path.join(self.path, 'README.md')

    @property
    def mlbox_file(self) -> str:
        return os.path.join(self.path, 'mlbox.yaml')

    @property
    def implementation_dir(self) -> str:
        return os.path.join(self.path, 'implementation')

    @property
    def workspace_dir(self) -> str:
        return os.path.join(self.path, 'workspace')

    @property
    def tasks_dir(self) -> str:
        return os.path.join(self.path, 'tasks')

    @property
    def implementation_file(self) -> str:
        return os.path.join(self.implementation_dir, 'mlbox_implementation.yaml')


class MLTask:
    def __init__(self, name: str):
        self.name: str = name  # A string, task name
        self.inputs = {}  # A dictionary from input name to a MLTaskInput
        self.outputs = {}  # A dictionary from output name to a MLTaskOutput
        self.defaults = {}  # A default param set name to MLTaskDefaults


class MLTaskInput:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc

    def __str__(self) -> str:
        return "MLTaskInput(name={}, desc={})".format(self.name, self.desc)

    __repr__ = __str__


class MLTaskOutput:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc

    def __str__(self) -> str:
        return "MLTaskOutput(name={}, desc={})".format(self.name, self.desc)

    __repr__ = __str__


class MLTaskDefaults:
    def __init__(self, name: str, default_paths: dict):
        self.name = name
        self.default_paths = default_paths  # task argument name to path

    def __str__(self) -> str:
        return "MLTaskDefaults(name={}, desc={})".format(self.name, self.default_paths)

    __repr__ = __str__


class SingularityImplementation(object):

    TYPE = 'singularity'

    def __init__(self, cfg: dict):
        self.recipe_path = None
        self.image_path = None


class DockerImplementation(object):
    """ A helper class to access docker-based runner parameters (mlbox_implementation.yaml). """

    TYPE = 'docker'

    def __init__(self, cfg: dict):
        self.dockerfile_path = None
        self.docker_runtime = cfg['docker_runtime']
        self.docker_args = cfg['docker_args']
        self.image = cfg['image']
        self.command = cfg['command']
        self.args = cfg['args']
        self.configure = cfg.get('configure', 'build')
        # Dictionary of task specific parameters that are assigned in __main__.py. This dict will be overwritten.
        self.task: dict = {}

    def __str__(self) -> str:
        return "DockerImplementation(dockerfile_path={}, image={}, docker_runtime={})".format(
            self.dockerfile_path, self.image, self.docker_runtime
        )


class PythonImplementation(object):
    """ A helper class to access python-based runner parameters (mlbox_implementation.yaml). """

    TYPE = 'python'

    def __init__(self, cfg: dict):
        self.force_reconfigure = cfg.get('force_reconfigure', False)
        self.interpreter = cfg.get('interpreter', 'current')
        self.virtualenv = cfg.get('virtualenv', None)
        self.conda = cfg.get('conda', None)
        self.system = cfg.get('system', {})
        self.pipenv = cfg.get('pipenv', None)
        self.requirements = cfg.get('requirements', None)
        self.entrypoint = cfg.get('entrypoint', None)

        if self.interpreter in (None, '', 'current'):
            self.interpreter = 'system'
            self.system = {'interpreter': sys.executable}

        self.system['interpreter'] = self.system.get('interpreter', None)
        if self.system['interpreter'] is None:
            self.system['interpreter'] = sys.executable

        self.task = None

    @property
    def interpreter_config(self) -> dict:
        config = getattr(self, self.interpreter, None)
        if config is None:
            raise ValueError("Incorrect Python interpreter ({})".format(self.interpreter))
        return config

    def __str__(self) -> str:
        return "PythonImplementation(interpreter={}, config={}, force_reconfigure={}, requirements={}, "\
               "entrypoint={})".format(self.interpreter, self.interpreter_config, self.force_reconfigure,
                                       self.requirements, self.entrypoint)
