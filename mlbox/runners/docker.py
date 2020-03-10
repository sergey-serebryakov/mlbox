import logging
from typing import List, Union

from mlbox.mlbox_local_run import run_or_die
from mlbox.runners.lib.docker_env import DockerEnv
from mlbox.runners.lib.runner import MLBoxRunner

logger = logging.getLogger(__name__)


class DockerRunner(MLBoxRunner):
    """ Local MLBox runner executes ML models on a local node: bare metal or docker containers. """

    MANDATORY_PARAMS = ['configure', 'image']

    def __init__(self, config: dict):
        """  """
        super(DockerRunner, self).__init__(config)
        missing_params = [param for param in DockerEnv.MANDATORY_PARAMS if param not in config]
        if len(missing_params) > 0:
            raise ValueError("Missing mandatory docker runner parameters: {}".format(missing_params))

    def configure(self):
        """ Configure a (remote) platform.
        TODO: We target docker runtime, so, possibly, check for docker/nvidia-docker and a container, data sets as well?
        """
        logger.info("Configuring MLBox: %s", str(self.config))
        docker = DockerEnv(self.config)

        logger.info("Checking if can run docker ... ")
        if not docker.is_docker_available():
            raise ValueError("Docker runtime is not available")

        logger.info("Checking if docker image exists ... ")
        if not docker.is_image_available():
            action = self.config['configure']
            if action == 'build':
                logger.info("Image does not exist, building ... ")
                docker.build()
            elif action == 'pull':
                logger.info("Image does not exist, pulling ... ")
                docker.pull()
            elif action == 'load':
                logger.info("Image does not exist, loading ... ")
                raise NotImplementedError("Not Implemented")
            else:
                raise ValueError("Unknown docker action for configure step ('{}').".format(action))
        else:
            logger.info("Image found (%s).", self.config['image'])

    def execute(self, cmd: Union[List[str], str]) -> int:
        """ Execute command `cmd` on a platform specified by `platform_config`.
        Args:
            cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
                specific platform described by `platform_config`.
        TODO: Should output be redirected to somewhere instead of just writing to standard output?
        """
        """
        cmd = MLBoxRunner.format_command(cmd)
        logging.info("Executing: %s", str(cmd))
        try:
            return subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        except subprocess.CalledProcessError as err:
            logging.warning("Error while executing MLBox: cmd=%s, err=%s", str(cmd), str(err))
            return err.returncode
        """
        volumes_str = ' '.join(['-v {}:{}'.format(t[0], t[1]) for t in self.config['mount_points'].items()])
        docker_args_str = ' '.join(['-e {}:{}'.format(t[0], t[1]) for t in self.config['run_args'].items()])
        args_str = ' '.join(sorted(['--{}={}'.format(k, v) for k, v in self.config['mlbox_args'].items()]))
        cmd = '{} run {} {} --rm --net=host --privileged=true -t {} {}'.format(
            self.config['docker_runtime'], volumes_str, docker_args_str, self.config['image'], args_str
        )
        run_or_die(cmd)
        return 0
