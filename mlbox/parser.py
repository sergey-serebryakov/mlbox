import os
import sys
import glob
from typing import Union
from mlbox.util import Utils
from mlbox.metadata import MLBox, DockerImplementation, SingularityImplementation, PythonImplementation, \
    ExecImplementation, MLTask, MLTaskInput, MLTaskOutput, MLTaskDefaults


class MLBoxParser(object):
    """ Given MLBox path and MLBox specifications, return a metadata object describing this MLBox. """

    @staticmethod
    def load_platform_config(file_name: Union[str, None]) -> dict:
        """ Load platform definition file.
        Args:
            file_name (str): FileName or FileName:Runner, for instance:  './platforms/platforms.yaml:python'
        Returns:
            A dictionary with parameters.
            TODO: If design OK, implement metadata classes for different platform configurations.

        Idea is to have a MLBox definition file that defines platform-independent parameters and a platform
        definition file that extends/adds new parameters. Platform definition configuration may contain such parameters
        as http proxy, user name and their passwords, host name for remote execution etc.
        """
        if file_name is None:
            return {}
        if file_name.endswith('.yaml'):
            file_name, default = file_name, None
        else:
            parts = file_name.split(':')
            file_name, default = parts[0], parts[1]
        config = Utils.load_yaml(file_name)
        # Runner configuration file may contain multiple platforms, select default one or the one requested by a user.
        if default is None:
            default = config['default']
        return config[default]

    @staticmethod
    def create_docker_metadata(mlbox: MLBox, impl: dict) -> MLBox:
        """ Wrap the 'impl' dictionary with DockerImplementation instance.
        The 'impl' is a dictionary loaded from mlbox_implementation.yaml file, that's specific to each runner.
        """
        mlbox.implementation = DockerImplementation(impl)
        mlbox.implementation.dockerfile_path = os.path.join(mlbox.implementation_dir, 'docker/dockerfiles/Dockerfile')
        mlbox.implementation_type = mlbox.implementation.TYPE
        return mlbox

    @staticmethod
    def create_singularity_metadata(mlbox: MLBox, impl: dict) -> MLBox:
        """ Wrap the 'impl' dictionary with SingularityImplementation instance.
        The 'impl' is a dictionary loaded from mlbox_implementation.yaml file, that's specific to each runner.
        """
        mlbox.implementation = SingularityImplementation(impl)
        mlbox.implementation.image_path = os.path.join(mlbox.implementation_dir,
                                                       'singularity/recipes/mlbox.simg')
        mlbox.implementation.recipe_path = os.path.join(mlbox.implementation_dir,
                                                        'singularity/recipes/Singularity.recipe')
        mlbox.implementation_type = mlbox.implementation.TYPE
        return mlbox

    @staticmethod
    def create_python_metadata(mlbox: MLBox, impl: dict) -> MLBox:
        """ Wrap the 'impl' dictionary with PythonImplementation instance.
        The 'impl' is a dictionary loaded from mlbox_implementation.yaml file, that's specific to each runner.
        """
        mlbox.implementation = PythonImplementation(impl)
        mlbox.implementation_type = mlbox.implementation.TYPE
        return mlbox

    @staticmethod
    def create_exec_metadata(mlbox: MLBox, impl: dict) -> MLBox:
        """ Wrap the 'impl' dictionary with ExecImplementation instance.
        The 'impl' is a dictionary loaded from mlbox_implementation.yaml file, that's specific to each runner.
        """
        mlbox.implementation = ExecImplementation(impl)
        mlbox.implementation_type = mlbox.implementation.TYPE
        return mlbox

    @staticmethod
    def create_metadata(box_dir: str) -> MLBox:
        """ Return MLBox meta data.
        Args:
            box_dir (str): Path to a MLBox.
        Returns:
            MLBox: MLBox metadata.
        """
        mlbox_path = os.path.abspath(box_dir)
        if not os.path.exists(mlbox_path):
            raise ValueError("MLBox path does not exist ({})".format(mlbox_path))
        mlbox = MLBox(mlbox_path)

        # Discover each task
        metadata = Utils.load_yaml(mlbox.mlbox_file)
        mlbox.set_name(metadata['name'])

        # The 'metadata' is a dictionary mapping task name to a dictionary with 'inputs'/'outputs' keys.
        for task_name in metadata['tasks']:
            task = metadata['tasks'][task_name]
            mltask = MLTask(task_name)
            for input_name in task['inputs']:
                task_input = task['inputs'][input_name]
                mltask.inputs[input_name] = MLTaskInput(input_name, task_input['description'])
            for output_name in task['outputs']:
                task_output = task['outputs'][output_name]
                mltask.outputs[output_name] = MLTaskOutput(output_name, task_output['description'])
            mlbox.tasks[task_name] = mltask

        # Parse MLBox implementation metadata (runner metadata - python/docker/ssh/k8s/...)
        impl = Utils.load_yaml(mlbox.implementation_file)
        if impl['implementation_type'] == 'docker':
            mlbox = MLBoxParser.create_docker_metadata(mlbox, impl)
        elif impl['implementation_type'] == 'python':
            mlbox = MLBoxParser.create_python_metadata(mlbox, impl)
        elif impl['implementation_type'] == 'singularity':
            mlbox = MLBoxParser.create_singularity_metadata(mlbox, impl)
        elif impl['implementation_type'] == 'exec':
            mlbox = MLBoxParser.create_exec_metadata(mlbox, impl)
        else:
            raise ValueError('Unsupported MLBox implementation ({}).'.format(impl['implementation_type']))

        # Find the defaults for tasks
        for task_name in os.listdir(mlbox.tasks_dir):
            if task_name not in mlbox.tasks:
                raise ValueError('WARNING: Found tasks/{} but no such task in mlbox.yaml'.format(task_name))
            # Find all yaml files in `mlbox.tasks_dir/task_name`.
            for config_file in glob.glob(os.path.join(mlbox.tasks_dir, task_name, '*.yaml')):
                defaults_name = os.path.basename(config_file)[:-5]
                # print("DefaultName: ", config_file, defaults_name)
                mlbox.tasks[task_name].defaults[defaults_name] = MLTaskDefaults(
                    name=defaults_name,
                    default_paths=Utils.load_yaml(config_file)
                )

        return mlbox

    @staticmethod
    def print_mlbox_metadata(mlbox: MLBox):
        print("MLBox name: {}".format(mlbox.name))
        print("  - Directory structure:")
        print("    - Path: {}".format(mlbox.path))
        print("    - Specs File: {}".format(mlbox.mlbox_file))
        print("    - ReadMe File: {}".format(mlbox.readme_file))
        print("    - Workspace Path: {}".format(mlbox.workspace_dir))
        print("  - Tasks (dir={}):".format(mlbox.tasks_dir))
        for task_name, task in mlbox.tasks.items():
            print("    - Name: {}".format(task.name))
            print("      - Inputs: {}".format(task.inputs))
            print("      - Outputs: {}".format(task.outputs))
            print("      - Defaults: {}".format(task.defaults))
        print("  - MLBox Runner Type (type={}, dir={}):".format(mlbox.implementation_type, mlbox.implementation_dir))
        print("      {}".format(mlbox.implementation))


def main():
    mlbox = MLBoxParser.create_metadata(sys.argv[1])
    MLBoxParser.print_mlbox_metadata(mlbox)


if __name__ == '__main__':
    main()
