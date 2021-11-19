import os
import abc
import shutil
import uuid
import logging
import tempfile
import typing as t
from omegaconf import (OmegaConf, DictConfig)


logger = logging.getLogger(__name__)


class MLCubeInstance(abc.ABC):
    """ Base class for different instantiations of MLCube (local, remote, directory, archive, container ...). """

    def materialize(self) -> None:
        """ Perform necessary actions to materialize MLCube instance in current directory if this is required.
        It is assumed, that once materialized, MLCube instance type could be `MLCubeDirectory`.
            - For instance, when URI is a GitHub repo, we might need to clone the repo.
            - If it's a docker image, we might need to extract `/mlcube` directory into current directory.
            - ...
        This can be done lazily, whenever a user calls `load_config` or `uri`. Or it can be done in the __init__ method.
        """
        pass

    @abc.abstractmethod
    def load_config(self) -> DictConfig:
        """ Load MLCube configuration file.
        This method is called by MLCube core library.

        Returns:
            MCube configuration as DictConfig object.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def uri(self) -> t.Text:
        """ Concrete semantics of this method are unclear. It can probably be a canonical version of what user supplied
        on a command line (--mlcube=MLCUBE_URI).
        """
        raise NotImplementedError


MLCubeInstanceType = t.TypeVar('MLCubeInstanceType', bound=MLCubeInstance)


class MLCubeDirectory(MLCubeInstance):
    """ An MLCube instantiation as a local directory. """
    def __init__(self, uri: t.Optional[t.Text] = None) -> None:
        if uri is None:
            uri = os.getcwd()
        uri = os.path.abspath(uri)
        if os.path.isfile(uri):
            self.path, self.file = os.path.split(uri)
        else:
            self.path, self.file = os.path.abspath(uri), 'mlcube.yaml'

    def load_config(self) -> DictConfig:
        config: DictConfig = OmegaConf.load(self.uri())
        if not isinstance(config, DictConfig):
            logger.warning(f"[{self.__class__}] MLCube configuration file is not a dictionary "
                           f"(path={self.path}, file={self.file}, type={type(config)})")
        return config

    def uri(self) -> t.Text:
        return os.path.join(self.path, self.file)


class MLCubeDockerImage(MLCubeInstance):
    def __init__(self, uri: t.Text) -> None:
        # Should be a canonical image name
        self.image = uri[7:] if uri.startswith('docker:') else uri
        # Once materialized, this should represent local directory-based MLCube
        self._mlcube: t.Optional[MLCubeDirectory] = None

    def materialize(self) -> None:
        if self._mlcube is not None:
            return

        # Keep these here to avoid circular dependencies.
        from mlcube.shell import Shell
        from mlcube.runner import Runner
        from mlcube.platform import Platform
        from mlcube.system_settings import SystemSettings

        # Load docker runner configuration from system settings files. Assumption is that user has configured
        # the default docker runner (platform=docker).
        system_settings = SystemSettings()
        docker_config: DictConfig = system_settings.get_platform('docker')
        if len(docker_config) == 0:
            raise RuntimeError(f"{self.__class__} MLCube docker runner not installed")
        runner_cls: t.Optional[t.Type[Runner]] = Platform.get_runner(
            system_settings.runners.get(docker_config.runner, None)
        )
        docker_config = OmegaConf.create(dict(runner=docker_config, docker=dict(image=self.image)))
        runner_cls.CONFIG.validate(docker_config)
        docker_config = docker_config.runner
        # Pull image if it does not exist.
        if not Shell.docker_image_exists(docker_config.docker, image=self.image):
            Shell.run(docker_config.docker, 'pull', self.image)
        # Extract directory-based MLCube from a docker image to a temporary local directory.
        with tempfile.TemporaryDirectory() as tmp_dir:
            container_name: t.Text = str(uuid.uuid4()).replace('-', '')
            Shell.run(
                docker_config.docker, 'run', '-d', '--rm', docker_config.cpu_args, docker_config.env_args,
                f'--name {container_name}', '--entrypoint sleep', self.image, 'infinity'
            )
            Shell.run(docker_config.docker, 'cp', f'{container_name}:/mlcube/', tmp_dir)
            Shell.run(docker_config.docker, 'rm', '-f', container_name)
            # Check if we have already materialized it.
            mlcube_tmp_path = os.path.join(tmp_dir, 'mlcube')
            if not os.path.exists(mlcube_tmp_path):
                raise RuntimeError(f"The docker image {self.image} does not provide MLCube information (no '/mlcube') "
                                   "directory found.")
            mlcube_name: t.Text = MLCubeDirectory(mlcube_tmp_path).load_config().name
            materialized_path: t.Text = os.path.join(os.getcwd(), mlcube_name)
            if os.path.exists(materialized_path):
                logger.info(f"{self.__class__} Found materialized MLCube in {materialized_path}.")
            else:
                shutil.move(mlcube_tmp_path, materialized_path)
                logger.info(f"{self.__class__} Materialized MLCube in {materialized_path}.")

            self._mlcube = MLCubeDirectory(materialized_path)

    def load_config(self) -> DictConfig:
        if self._mlcube is None:
            self.materialize()
        return self._mlcube.load_config()

    def uri(self) -> t.Text:
        if self._mlcube is None:
            self.materialize()
        return self._mlcube.uri()


class CliParser(object):
    @staticmethod
    def parse_mlcube_arg(mlcube: t.Optional[t.Text]) -> MLCubeInstanceType:
        """ Parse value of the `--mlcube` command line argument.
        Args:
            mlcube: Path to a MLCube directory or `mlcube.yaml` file. If it's a directory, standard name
                `mlcube.yaml` is assumed for MLCube definition file.
        Returns:
            One of child classes of MLCubeInstance that represents this MLCube.
        """
        if mlcube is None:
            mlcube = os.getcwd()
        if mlcube.startswith('docker:'):
            return MLCubeDockerImage(mlcube)
        return MLCubeDirectory(mlcube)

    @staticmethod
    def parse_list_arg(arg: t.Optional[t.Text], default: t.Optional[t.Text] = None) -> t.List[t.Text]:
        """ Parse a string into list of strings using `,` as a separator.
        Args:
            arg: String if elements separated with `,`.
            default: Default value for `arg` if `arg` is None or empty.
        Returns:
            List of items.
        """
        arg = arg or default
        if not arg:
            return []
        return arg.split(',')

    @staticmethod
    def parse_extra_arg(*args: t.Text) -> t.Tuple[DictConfig, t.Dict]:
        """ Parse extra arguments on a command line.
        These arguments correspond to:
            - MLCube runtime arguments. These start with `-P` prefix and are translated to a nested dictionaries
                structure using `.` as a separator. For instance, `-Pdocker.image=mlcommons/mnist:0.0.1` translates to
                python dictionary {'docker': {'image': 'mlcommons/mnist:0.0.1'}}.
            - Task arguments are all other arguments that do not star with `-P`. These arguments are input/output
                arguments of tasks.
        Args:
            args: List of arguments that have not been parsed before.
        Returns:
            Tuple of two dictionaries: (mlcube_arguments, task_arguments).
        """
        mlcube_args = OmegaConf.from_dotlist([arg[2:] for arg in args if arg.startswith('-P')])

        task_args = [arg.split('=') for arg in args if not arg.startswith('-P')]
        task_args = {arg[0]: arg[1] for arg in task_args}

        return mlcube_args, task_args
