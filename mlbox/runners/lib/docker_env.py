"""
DockerUtils is based on Validator class from here:
    https://github.com/HewlettPackard/dlcookbook-dlbs/blob/master/python/dlbs/validator.py#L282
"""
import copy
import subprocess
# import sys

from mlbox.mlbox_local_run import run_or_die


class DockerEnv(object):

    MANDATORY_PARAMS = ['image', 'mlbox_path']
    OPTIONAL_PARAMS = {'docker_runtime': 'docker', 'build_args': [], 'run_args': []}

    def __init__(self, config: dict):
        missing_params = [param for param in DockerEnv.MANDATORY_PARAMS if param not in config]
        if len(missing_params) > 0:
            raise ValueError("Missing mandatory docker runner parameters: {}".format(missing_params))

        self.__config = copy.deepcopy(config)
        for name, value in DockerEnv.OPTIONAL_PARAMS.items():
            self.__config[name] = self.__config.get(name, value)

    @property
    def config(self):
        return self.__config

    def pull(self) -> bool:
        """ Pull an image - initial implementation.
        It may take substantial amount of time to complete this command, so output is printed out immediately.
        """
        cmd = ['docker', 'pull', self.config['image']]
        """
        try:

            ret_code = subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        except subprocess.CalledProcessError as err:
            ret_code = err.returncode
        return ret_code == 0
        """
        run_or_die(' '.join(cmd))
        return True

    def build(self) -> bool:
        """ Build an image - initial implementation.
        It may take substantial amount of time to complete this command, so output is printed out immediately.
        """

        cmd = ['cd', self.config['mlbox_path'], ';', 'docker', 'build']
        build_args = self.config['build_args']
        for arg in build_args:
            cmd.extend(['--build-arg', '{}={}'.format(arg, build_args[arg])])
        cmd.extend(['-t', self.config['image'], '-f', 'implementation/docker/dockerfiles/Dockerfile', '.'])
        """
        try:
            ret_code = subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        except subprocess.CalledProcessError as err:
        return ret_code == 0
            ret_code = err.returncode
        """
        run_or_die(' '.join(cmd))
        return True

    def is_docker_available(self) -> bool:
        """ Checks if MLBox can run docker/nvidia-docker/nvidia-docker2. """
        runtime = self.config['docker_runtime']
        if runtime == 'docker' and '--runtime=nvidia' in self.config['run_args']:
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
                ret_code, output = DockerEnv.run_process(cmd)
                if ret_code == 0 and 'nvidia' not in _get_docker_runtimes(output):
                    ret_code = -1
            elif runtime in ['docker', 'runc']:
                ret_code, output = DockerEnv.run_process(["docker", "--version"])
            elif runtime in ['nvidia-docker', 'nvidia_docker']:
                ret_code, output = DockerEnv.run_process(["nvidia-docker", "--version"])
            else:
                ret_code = 1
        except OSError:
            ret_code = 1

        return ret_code == 0

    def is_image_available(self) -> bool:
        """ Checks if this docker image exists. """
        try:
            docker_image = self.config['image']
            cmd = ["docker", "inspect", "--type=image", docker_image]
            ret_code, output = DockerEnv.run_process(cmd)
        except OSError:
            ret_code = 1
        return ret_code == 0

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
