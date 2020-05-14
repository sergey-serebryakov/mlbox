import os
import logging
from typing import Union, List
from mlbox import metadata
from mlbox.runners.mlbox_runner import MLBoxRunner
from mlbox.util import Utils


logger = logging.getLogger(__name__)


class SingularityRunner(MLBoxRunner):
    def __init__(self, mlbox: metadata.MLBox, platform_config: dict):
        """  """
        super(SingularityRunner, self).__init__({})
        self.mlbox = mlbox
        self.platform_config = platform_config
        if self.mlbox.implementation_type != 'singularity':
            raise ValueError("Incorrect implementation type ({})".format(self.mlbox.implementation_type))
        if not isinstance(self.mlbox.implementation, metadata.SingularityImplementation):
            raise ValueError("Incorrect metadata ({})".format(type(self.mlbox.implementation)))

    def configure(self):
        image = self.mlbox.implementation.image_path
        if os.path.exists(image):
            logger.info("Image found (%s).", image)
            return

        recipe = self.mlbox.implementation.recipe_path
        mlbox_root = self.mlbox.path
        cmd = "cd {}; singularity build --fakeroot '{}' '{}'".format(mlbox_root, image, recipe)
        Utils.run_or_die(cmd)

    def execute(self, cmd: Union[List[str], str]) -> int:
        """  """
        mount_points = self.mlbox.implementation.task['mount_points']
        mlbox_args = self.mlbox.implementation.task['mlbox_args']

        volumes_str = ' '.join(['--bind {}:{}'.format(t[0], t[1]) for t in mount_points.items()])
        args_str = ' '.join(sorted(['--{}={}'.format(k, v) for k, v in mlbox_args.items()]))
        image = self.mlbox.implementation.image_path

        # Let's assume singularity containers provide entry point in the right way.
        cmd = "singularity run {} {} {}".format(volumes_str, image, args_str)
        logger.info(cmd)
        Utils.run_or_die(cmd)
        return 0
