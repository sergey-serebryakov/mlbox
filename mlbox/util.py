import os
import sys
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class Utils(object):
    @staticmethod
    def load_yaml(path: str):
        with open(path) as stream:
            return yaml.load(stream.read(), Loader=Loader)

    @staticmethod
    def get_volumes_and_paths(inputs):
        """Given a bunch of local paths on the host. Determine where the containing
        directories need to be mounted in the docker.

        For Example,
        ['/home/me/foo/bar', '/home/me/foo/bar2', '/home/me/whiz/bang']
        Becomes
        {'/home/me/foo': '/input0', '/home/me/whiz': '/input1'},
        {'/home/me/foo/bar': '/input0/bar',
         '/home/me/foo/bar2': '/input0/bar2',
         '/home/me/whiz/bang': '/input1/bang'}
        """
        dir_map = {}
        path_map = {}
        for i, input_path in enumerate(inputs):
            outer_dir = os.path.dirname(input_path)
            if outer_dir not in dir_map:
                dir_map[outer_dir] = '/input{}'.format(i)
            path_map[input_path] = os.path.join(dir_map[outer_dir], os.path.basename(input_path))
        return dir_map, path_map

    @staticmethod
    def run_docker(docker_name: str, input_map: dict):
        """Prints the command to run the docker

        Example input_map:
        {'params': 'tasks/big_run/input/params.yaml', ...}
        """
        volumes, mapped_inputs = Utils.get_volumes_and_paths(input_map.values())
        print('volumes: ', volumes)
        print('mapped_inputs:', mapped_inputs)
        volumes_str = ' '.join(
            ['-v {}:{}'.format(t[0], t[1]) for t in volumes.items()])
        arguments = []
        for input_name in input_map:
            inner_path = mapped_inputs[input_map[input_name]]
            arguments.append('--{}={}'.format(input_name, inner_path))
        cmd = 'sudo docker run {} --net=host --privileged=true -t {} {}'.format(
            volumes_str, docker_name, ' '.join(arguments))
        print(cmd)
        # ensure failure is shown to caller.
        # if os.system(cmd) != 0:
        #     sys.exit(1)

    @staticmethod
    def get_commandline_args(mlbox: str = None, user_args: list = None):
        """Parses command line.
        For example:
            box/path:TASK/params --params=/foo/bar
        Becomes:
            'box/path', {'params': '/foo/bar'}
        """
        mlbox = mlbox if mlbox is not None else sys.argv[1]
        parts = mlbox.split(':')
        mlbox_dir = parts[0]
        if len(parts) == 1:
            task = input_group = None
        else:
            task_and_inputs = parts[1]
            task_and_inputs = task_and_inputs.split('/')
            if len(task_and_inputs) == 1:
                task, input_group = task_and_inputs[0], 'default'
            elif len(task_and_inputs) == 2:
                task, input_group = task_and_inputs
            else:
                raise ValueError("Wrong task specification ({})".format(parts[1]))

        io = {}
        user_args = user_args if user_args is not None else sys.argv[2:]
        for arg in user_args:
            args = arg.split('=')
            name = args[0].strip('--')
            val = args[1]
            print(name, val)
            io[name] = val
        return mlbox_dir, task, input_group, io

    @staticmethod
    def construct_docker_command_with_default_inputs(mlbox_dir, task_name, input_group, override_paths):
        """
            TODO: this function isn't perfect, this just demonstrates the basic idea
            This function will need to be modified to work reliably  (or at all)
        """
        # volume_map = {}

        task_metadata = mlbox_dir.task_metadata(task_name)
        print(task_metadata)

        names_to_paths = {}

        # determine the input paths
        for input_name in task_metadata['inputs']:
            if input_name in override_paths:
                path = override_paths[input_name]
            else:
                path = mlbox_dir.get_default_input_path(task_name, input_group, input_name)
            path = os.path.abspath(path)
            names_to_paths[input_name] = path

        outputs_directory = mlbox_dir.outputs_directory(task_name, input_group)
        for output_name in task_metadata['outputs']:
            if output_name in override_paths:
                path = override_paths[output_name]
            else:
                path = os.path.join(outputs_directory, output_name)
            path = os.path.abspath(path)
            names_to_paths[output_name] = path

        print(mlbox_dir.standard_docker_metadata)
        Utils.run_docker(mlbox_dir.standard_docker_metadata['container']['image'], names_to_paths)

    @staticmethod
    def construct_docker_run_command(mlbox, mount_volumes, kw_args, run_args=None) -> str:
        volumes_str = ' '.join(['-v {}:{}'.format(t[0], t[1]) for t in mount_volumes.items()])
        run_args = run_args if run_args is not None else {}
        docker_args_str = ' '.join(['-e {}:{}'.format(t[0], t[1]) for t in run_args.items()])
        args_str = ' '.join(sorted(['--{}={}'.format(k, v) for k, v in kw_args.items()]))
        cmd = 'sudo {} run {} {} --net=host --privileged=true -t {} {}'.format(
            mlbox.implementation.docker_runtime, volumes_str, docker_args_str, mlbox.implementation.image, args_str
        )
        return cmd

    @staticmethod
    def construct_docker_build_command(mlbox_root: str, image_name: str) -> str:
        return 'cd {}; sudo docker build -t {} -f implementation/docker/dockerfiles/Dockerfile .'.format(mlbox_root,
                                                                                                         image_name)

    @staticmethod
    def get_args_with_defaults(mlbox, overrides, task_name, defaults=None) -> dict:
        """Returns an argument map, {'arg_name': '/path/to/file'}"""
        args = {}
        task: dict = mlbox.tasks[task_name]
        task_args: list = list(task.inputs.keys()) + list(task.outputs.keys())

        # print("Defaults: ", defaults)  # A string
        # print("Task.Inputs: ", task.inputs)  # Mapping from a name to a MLTaskInput(name, desc)
        # print("Task.Outputs: ", task.outputs)  # Mapping from a name to a MLTaskOutput(name, desc)
        # print("Task.Defaults: ", task.defaults)
        # print("Overrides: ", overrides)  # Almost always empty

        for task_arg in task_args:
            if task_arg in overrides:
                args[task_arg] = overrides[task_arg]
            elif defaults not in task.defaults:
                print('Checked task: {}'.format(task.name))
                raise Exception('No such defaults for: {}'.format(defaults))
            elif task_arg not in task.defaults[defaults].default_paths:
                raise Exception('Defaults for {} does not include {}.'.format(defaults, task_arg))
            else:
                args[task_arg] = os.path.join(mlbox.workspace_dir, task.defaults[defaults].default_paths[task_arg])
        return args

    @staticmethod
    def run_or_die(cmd):
        print(cmd)
        if os.system(cmd) != 0:
            raise Exception('Command failed: {}'.format(cmd))
