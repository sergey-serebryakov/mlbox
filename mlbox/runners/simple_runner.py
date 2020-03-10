import sys
import logging

from mlbox import mlbox_parser
from mlbox.mlbox_local_run import get_commandline_args, get_args_with_defaults, get_volumes_and_paths
from mlbox.runners.docker import DockerRunner
from mlbox.runners.lib.runner import RunnerConfig
from mlbox.runners.ssh import SSHRunner

logging.basicConfig(level=logging.INFO, format="[MLBOX] %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) == 3:
        action, runner, mlbox = sys.argv[1], None, sys.argv[2]
    elif len(sys.argv) == 4:
        action, runner, mlbox = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        raise ValueError("usage: {} configure|run [runner] mlbox".format(sys.argv[0]))

    if action not in ('configure', 'run'):
        raise ValueError("wrong action: {}".format(action))
    logger.info("mlbox: %s, action: %s, runner: %s", mlbox, action, runner)

    # If exists, load runner configuration
    runner_config = RunnerConfig.load(runner)
    logger.info("runner loaded: %s", str(runner_config))

    # Split command line arguments into parts - no configuration files required
    mlbox_dir, task_name, input_group, io = get_commandline_args(mlbox=mlbox, user_args=[])
    logger.info("mlbox_dir=%s, task_name=%s, input_group=%s, io=%s", mlbox_dir, task_name, input_group, str(io))

    # Retrieve MLBox metadata - this reads MLBox config files and supports docker implementations.
    mlbox = mlbox_parser.create_metadata(mlbox_dir)
    logger.info("name=%s, path=%s, implementation_type=%s, implementation=%s", mlbox.name, mlbox.path,
                mlbox.implementation_type, mlbox.implementation)

    #
    run_type = "{}/{}".format(runner_config['runner'], mlbox.implementation_type)

    # Sort of temporary solution
    if action == 'configure':
        impl = mlbox.implementation
        if run_type == 'docker/docker':
            config = {'mlbox_path': mlbox_dir, 'image': impl.image, 'build_args': [], 'run_args': [],
                      'docker_runtime': impl.docker_runtime, 'configure': impl.configure}
            config.update(runner_config)
            DockerRunner(config).configure()
        elif run_type == 'ssh/docker':
            config = {'mlbox_path': mlbox_dir}
            config.update(runner_config)
            SSHRunner(config).configure()
        else:
            raise ValueError("Unsupported mlbox/runner specification: {}/{}".format(
                mlbox.implementation_type, runner_config['runner'])
            )
        return

    # Get task arguments with their default values
    args = get_args_with_defaults(mlbox, io, task_name, input_group)
    logger.info("Task=%s, args=%s", task_name, str(args))

    # dir_map is host dir to mount point within docker (i.e. volumes and mount points)
    # path_map is a map from host paths to internal docker paths
    dir_map, path_map = get_volumes_and_paths(args.values())
    logger.info("Host to docker directory mappings: %s", str(dir_map))
    logger.info("Host to docker file path mappings: %s", str(path_map))

    internal_args = {name: path_map[args[name]] for name in args}
    internal_args['mlbox_task'] = task_name
    logger.info("Internal args %s", str(internal_args))

    impl = mlbox.implementation
    if run_type == 'docker/docker':
        config = {'mlbox_path': mlbox_dir, 'image': impl.image, 'docker_runtime': impl.docker_runtime,
                  'configure': impl.configure, 'build_args': [], 'run_args': [], 'mount_points': dir_map,
                  'mlbox_args': internal_args}
        config.update(runner_config)
        runner = DockerRunner(config)
    elif run_type == 'ssh/docker':
        config = {'mlbox_path': mlbox_dir, 'remote_task': task_name, 'remote_input_group': input_group}
        config.update(runner_config)
        runner = SSHRunner(config)
    else:
        raise ValueError("Unsupported MLBox implementation: {}".format(mlbox.implementation_type))
    runner.execute("")


if __name__ == '__main__':
    main()
