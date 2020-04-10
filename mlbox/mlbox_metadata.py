import sys
import os


class MLBox:
    def __init__(self, path, tasks=None):
        # Maps name to MLTask
        self.name = None
        self.path = path
        self.tasks = {}
        if tasks:
            self.tasks = tasks

        self.implementation_type = None
        self.implementation = None

    def set_name(self, name):
        self.name = name

    def get_task(self, name):
        return self.tasks[name]

    @property
    def readme_file(self):
        return os.path.join(self.path, 'README.md')

    @property
    def mlbox_file(self):
        return os.path.join(self.path, 'mlbox.yaml')

    @property
    def implementation_dir(self):
        return os.path.join(self.path, 'implementation')

    @property
    def workspace_dir(self):
        return os.path.join(self.path, 'workspace')

    @property
    def tasks_dir(self):
        return os.path.join(self.path, 'tasks')

    @property
    def implementation_file(self):
        return os.path.join(self.implementation_dir, 'mlbox_implementation.yaml')


class MLTask:
    def __init__(self, name):
        self.name = name
        self.inputs = {}
        self.outputs = {}
        self.defaults = {}


class MLTaskInput:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc


class MLTaskOutput:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc


class MLTaskDefaults:
    def __init__(self, name, default_paths):
        self.name = name
        self.default_paths = default_paths


class DockerImplementation:
    def __init__(self):
        self.dockerfile_path = None
        self.docker_runtime = None
        self.docker_args = None
        self.image = None
        self.command = None
        self.args = None
        self.configure = None

    def set_from_dict(self, d):
        self.docker_runtime = d['docker_runtime']
        self.docker_args = d['docker_args']
        self.image = d['image']
        self.command = d['command']
        self.args = d['args']
        self.configure = d.get('configure', 'build')

    def __str__(self):
        return "DockerImplementation(dockerfile_path={}, image={}, docker_runtime={})".format(
            self.dockerfile_path, self.image, self.docker_runtime
        )


class PythonImplementation(object):

    TYPE = 'python'

    def __init__(self, cfg: dict):
        self.force_reconfigure = cfg.get('force_reconfigure', False)
        self.interpreter = cfg.get('interpreter', 'current')
        self.virtualenv = cfg.get('virtualenv', None)
        self.conda = cfg.get('conda', None)
        self.system = cfg.get('system', None)
        self.pipenv = cfg.get('pipenv', None)
        self.requirements = cfg.get('requirements', None)
        self.entrypoint = cfg.get('entrypoint', None)

        if self.interpreter in (None, '', 'current'):
            self.interpreter = 'system'
            self.system = {'interpreter': sys.executable}

        self.task = None

    @property
    def interpreter_config(self) -> dict:
        config = getattr(self, self.interpreter, None)
        if config is None:
            raise ValueError("Incorrect Python interpreter ({})".format(self.interpreter))
        return config

    def __str__(self):
        return "PythonImplementation(interpreter={}, config={}, force_reconfigure={}, requirements={}, "\
               "entrypoint={})".format(self.interpreter, self.interpreter_config, self.force_reconfigure,
                                       self.requirements, self.entrypoint)
