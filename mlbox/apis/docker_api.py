import copy
import logging
import subprocess
import os
from typing import Union
from mlbox import metadata
from mlbox.util import Utils


logger = logging.getLogger(__name__)


class DockerAPI(object):

    def __init__(self, mlbox: metadata.MLBox, platform_config: dict):
        self.mlbox = mlbox
        self.platform_config = copy.deepcopy(platform_config)
        if not isinstance(self.mlbox.implementation, metadata.DockerImplementation):
            raise ValueError("Incorrect metadata ({})".format(type(self.mlbox.implementation)))

    def pull(self) -> bool:
        """ Pull an image - initial implementation.
        It may take substantial amount of time to complete this command, so output is printed out immediately.
        """
        cmd = ['docker', 'pull', self.mlbox.implementation.image]
        Utils.run_or_die(' '.join(cmd))
        return True

    def build(self) -> bool:
        """ Build an image - initial implementation.
        It may take substantial amount of time to complete this command, so output is printed out immediately.
        """
        cmd = ['cd', self.mlbox.path, ';', 'docker', 'build']
        build_args = self.platform_config.get('build_args', {})

        for proxy_var in ('http_proxy', 'https_proxy'):
            if proxy_var not in build_args and os.environ.get(proxy_var, None) is not None:
                build_args[proxy_var] = os.environ[proxy_var]
                logger.warning("Setting docker build arg from env variable: {} = {}".format(proxy_var,
                                                                                            build_args[proxy_var]))

        for arg in build_args:
            cmd.extend(['--build-arg', '{}={}'.format(arg, build_args[arg])])
        cmd.extend(['-t', self.mlbox.implementation.image, '-f', 'implementation/docker/dockerfiles/Dockerfile', '.'])
        Utils.run_or_die(' '.join(cmd))
        return True

    def is_docker_available(self, runtime: Union[None, str] = None) -> bool:
        """ Checks if MLBox can run docker/nvidia-docker/nvidia-docker2. """

        if runtime is None:
            runtime = self.mlbox.implementation.docker_runtime
        if runtime == 'docker' and '--runtime=nvidia' in self.platform_config.get('run_args', {}):
            runtime = "nvidia_docker2"

        def _get_docker_runtimes(info):
            for line in info:
                line = line.strip()
                if line.startswith('Runtimes:'):
                    return line[9:].strip().split()
            return []

        try:
            if runtime in ['nvidia', 'nvidia-docker2', 'nvidia_docker2']:
                cmd = ["docker", "info"]
                ret_code, output = DockerAPI.run_process(cmd)
                if ret_code == 0 and 'nvidia' not in _get_docker_runtimes(output):
                    ret_code = -1
            elif runtime in ['docker', 'runc']:
                ret_code, output = DockerAPI.run_process(["docker", "--version"])
            elif runtime in ['nvidia-docker', 'nvidia_docker']:
                ret_code, output = DockerAPI.run_process(["nvidia-docker", "--version"])
            else:
                ret_code = 1
        except OSError:
            ret_code = 1

        return ret_code == 0

    def is_image_available(self) -> bool:
        """ Checks if this docker image exists. """
        try:
            docker_image = self.mlbox.implementation.image
            cmd = ["docker", "inspect", "--type=image", docker_image]
            ret_code, output = DockerAPI.run_process(cmd)
        except OSError:
            ret_code = 1
        return ret_code == 0

    def get_runtime(self):
        runtime = self.mlbox.implementation.docker_runtime
        if self.is_docker_available(runtime=runtime):
            return runtime
        if runtime == 'nvidia-docker' and self.is_docker_available(runtime='docker'):
            return 'docker'
        return runtime

    @staticmethod
    def run_process(cmd, env=None):
        """Runs process with subprocess.Popen (run a test).
        Args:
            cmd (list): A command with its arguments to run.
            env (dict): Environmental variables to initialize environment.
        Returns:
            tuple: (return_code (int), command_output (list of strings))
        """
        process = subprocess.Popen(cmd, universal_newlines=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, env=env)
        output = []
        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                output.append(line)
        return process.returncode, output
