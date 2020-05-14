from mlbox.metadata import MLBox


class RunnersFactory(object):
    @staticmethod
    def create(mlbox: MLBox, platform_config: dict):
        runner_type = platform_config.get('runner', mlbox.implementation_type)
        runner = None

        if runner_type == 'python':
            from mlbox.runners.python_runner import PythonRunner
            runner = PythonRunner(mlbox, platform_config)
        elif runner_type == 'docker':
            from mlbox.runners.docker_runner import DockerRunner
            runner = DockerRunner(mlbox, platform_config)
        elif runner_type == 'singularity':
            from mlbox.runners.singularity_runner import SingularityRunner
            runner = SingularityRunner(mlbox, platform_config)
        elif runner_type == 'ssh':
            from mlbox.runners.ssh_runner import SSHRunner
            runner = SSHRunner(mlbox, platform_config)

        if runner is None:
            raise ValueError("Invalid runner: {}".format(runner_type))
        return runner
