import logging
import sys
from datetime import datetime
from mlbox.parser import MLBoxParser
from mlbox.runners import RunnersFactory
from mlbox.util import Utils
from mlbox.help import Help


logging.basicConfig(level=logging.INFO, format="[MLBOX] %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def main():
    """
    https://groups.google.com/forum/#!topic/mlperf-best-practices/dObX9NvcUuc
    Usage:
      $ python -m mlbox COMMAND [PLATFORM_FILE[:RUNNER]] MLBOX_PATH[:TASK[/PARAM_SET]]
    Where:
      COMMAND          mandatory    One of [configure, run].
      PLATFORM_FILE    optional     Path to platform configuration file (yaml).
      RUNNER           optional     A runner to use that is defined in platform configuration file.
      MLBOX_PATH       mandatory    Path to a MLBox directory.
      TASK             optional     Mandatory for 'run' action. Task to execute.
      PARAM_SET        optional     Mandatory for 'run' action. Parameter set to use.
    Examples:
      $ python -m mlbox describe ./examples/hello_world/baremetal
      $ python -m mlbox configure ./examples/hello_world/baremetal
      $ python -m mlbox run ./examples/hello_world/baremetal:hello/xinyuan
      $ python -m mlbox run ./examples/hello_world/baremetal:goodbye/xinyuan

      $ python -m mlbox describe ./examples/hello_world/docker
      $ python -m mlbox configure ./examples/hello_world/docker
      $ python -m mlbox run ./examples/hello_world/docker:hello/xinyuan
      $ python -m mlbox run ./examples/hello_world/docker:goodbye/xinyuan

      $ python -m mlbox describe ./examples/hello_world/singularity
      $ https_proxy=${http_proxy} python -m mlbox configure ./examples/hello_world/singularity
      $ python -m mlbox run ./examples/hello_world/singularity:hello/xinyuan
      $ python -m mlbox run ./examples/hello_world/singularity:goodbye/xinyuan
    """
    # Parse command line arguments, see if mlbox needs to print help message
    if len(sys.argv) >= 2 and sys.argv[1] == 'help':
        Help.help(sys.argv[2:])
        return
    elif len(sys.argv) == 3:
        command, platform, mlbox = sys.argv[1], None, sys.argv[2]
    elif len(sys.argv) == 4:
        command, platform, mlbox = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        Help.generic_help_message()
        return

    # Parse MLBox metadata.
    # TODO: This is probably where mlbox needs to validate directory structure
    if command not in ('configure', 'run', 'describe'):
        raise ValueError("wrong command: {}".format(command))
    logger.info("mlbox: %s, command: %s, platform: %s", mlbox, command, platform)

    # Split command line arguments into parts - no configuration files required
    mlbox_dir, task_name, input_group, io = Utils.get_commandline_args(mlbox=mlbox, user_args=[])
    logger.info("mlbox_dir=%s, task_name=%s, input_group=%s, io=%s", mlbox_dir, task_name, input_group, str(io))

    # Retrieve MLBox metadata - this reads MLBox config files and supports docker implementations.
    mlbox = MLBoxParser.create_metadata(mlbox_dir)
    logger.info("name=%s, path=%s, implementation_type=%s, implementation=%s", mlbox.name, mlbox.path,
                mlbox.implementation_type, mlbox.implementation)

    # If exists, load runner configuration. We need to know which runner to use, so if a user did not specify a platform
    # a platform file, then use `implementation` form a mlbox.yaml file.
    platform_config = MLBoxParser.load_platform_config(platform)
    if not platform_config:
        # If custom runner was not specified, use the one associated with the MLBox implementation.
        platform_config = {'runner': mlbox.implementation_type}
    logger.info("platform/runner configuration: %s", str(platform_config))

    # Some commands do not require `task_name` argument which is null.
    # TODO: refactor me - maybe, update `get_args_with_defaults`/`get_volumes_and_paths` to work with emtpy/none args.
    if command == 'describe':
        MLBoxParser.print_mlbox_metadata(mlbox)
        return
    elif command == 'configure':
        runner = RunnersFactory.create(mlbox, platform_config)
        runner.configure()
        return

    # TODO: refactor me! The usage of task is super confusing. Difference between input_params/mlbox_args?
    if mlbox.implementation_type in ('python', 'exec'):
        args = Utils.get_args_with_defaults(mlbox, io, task_name, input_group)
        mlbox.implementation.task = {'name': task_name, 'input_group': input_group, 'input_params': args}
    elif mlbox.implementation_type in ('docker', 'singularity'):
        args = Utils.get_args_with_defaults(mlbox, io, task_name, input_group)
        dir_map, path_map = Utils.get_volumes_and_paths(args.values())

        internal_args = {name: path_map[args[name]] for name in args}
        internal_args['mlbox_task'] = task_name

        logger.info("Host to container directory mappings: %s", str(dir_map))
        logger.info("Host to container file path mappings: %s", str(path_map))
        logger.info("Internal args %s", str(internal_args))

        mlbox.implementation.task = {'name': task_name, 'input_group': input_group, 'input_params': internal_args,
                                     'mount_points': dir_map}

    # Run commands.
    if command == 'run':
        runner = RunnersFactory.create(mlbox, platform_config)
        logger.info("MLBox started at {}".format(str(datetime.now())))
        runner.execute(cmd=None)
        logger.info("MLBox finished at {}".format(str(datetime.now())))
    else:
        raise ValueError("Invalid command: {}".format(command))


if __name__ == '__main__':
    main()
