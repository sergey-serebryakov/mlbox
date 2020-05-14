import os
import logging
from typing import List, Union
from mlbox import metadata
from mlbox.apis.docker_api import DockerAPI
from mlbox.runners.mlbox_runner import MLBoxRunner
from mlbox.util import Utils


logger = logging.getLogger(__name__)


class DockerRunner(MLBoxRunner):
    """ Local MLBox runner executes ML models on a local node: bare metal or docker containers. """

    MANDATORY_PARAMS = ['configure', 'image']

    def __init__(self, mlbox: metadata.MLBox, platform_config: dict):
        """  """
        super(DockerRunner, self).__init__({})
        self.mlbox = mlbox
        self.platform_config = platform_config
        if self.mlbox.implementation_type != 'docker':
            raise ValueError("Incorrect implementation type ({})".format(self.mlbox.implementation_type))
        if not isinstance(self.mlbox.implementation, metadata.DockerImplementation):
            raise ValueError("Incorrect metadata ({})".format(type(self.mlbox.implementation)))

    def configure(self):
        """ Configure a (remote) platform.
        TODO: We target docker runtime, so, possibly, check for docker/nvidia-docker and a container, data sets as well?
        """
        logger.info("Configuring MLBox")
        docker = DockerAPI(self.mlbox, self.platform_config)

        logger.info("Checking if can run docker ... ")
        if not docker.is_docker_available():
            runtime = self.mlbox.implementation.docker_runtime
            if runtime == 'nvidia-docker':
                if not docker.is_docker_available(runtime='docker'):
                    raise ValueError("NVIDIA docker runtime is requested, but docker/nvidia-docker are not available")
                logger.warning("NVIDIA docker runtime is requested, it is not available, but docker runtime "
                               "is installed. Will continue to use docker.")

        logger.info("Checking if docker image exists ... ")
        if not docker.is_image_available():
            command = self.mlbox.implementation.configure
            if command == 'build':
                logger.info("Image does not exist, building ... ")
                docker.build()
            elif command == 'pull':
                logger.info("Image does not exist, pulling ... ")
                docker.pull()
            elif command == 'load':
                logger.info("Image does not exist, loading ... ")
                raise NotImplementedError("Not Implemented")
            else:
                raise ValueError("Unknown docker command for configure step ('{}').".format(command))
        else:
            logger.info("Image found (%s).", self.mlbox.implementation.image)

    def execute(self, cmd: Union[List[str], str]) -> int:
        """ Execute command `cmd` on a platform specified by `platform_config`.
        Args:
            cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
                specific platform described by `platform_config`.
        TODO: Should output be redirected to somewhere instead of just writing to standard output?
        """
        mount_points = self.mlbox.implementation.task['mount_points']
        run_args = self.mlbox.implementation.task.get('run_args', {})
        mlbox_args = self.mlbox.implementation.task['mlbox_args']

        for proxy_var in ('http_proxy', 'https_proxy'):
            if proxy_var not in run_args and os.environ.get(proxy_var, None) is not None:
                run_args[proxy_var] = os.environ[proxy_var]
                logger.warning("Setting docker build arg from env variable: {} = {}".format(proxy_var,
                                                                                            run_args[proxy_var]))
        docker = DockerAPI(self.mlbox, self.platform_config)
        runtime = docker.get_runtime()
        if runtime != self.mlbox.implementation.docker_runtime:
            logger.warning("Requested docker runtime '%s' is not installed, but '%s' is installed. "
                           "Will use it.", self.mlbox.implementation.docker_runtime, runtime)

        volumes_str = ' '.join(['-v {}:{}'.format(t[0], t[1]) for t in mount_points.items()])
        docker_args_str = ' '.join(['-e {}={}'.format(t[0], t[1]) for t in run_args.items()])
        args_str = ' '.join(sorted(['--{}={}'.format(k, v) for k, v in mlbox_args.items()]))
        cmd = '{} run {} {} --rm --net=host --privileged=true -t {} {}'.format(
            runtime, volumes_str, docker_args_str, self.mlbox.implementation.image, args_str
        )
        Utils.run_or_die(cmd)
        return 0
