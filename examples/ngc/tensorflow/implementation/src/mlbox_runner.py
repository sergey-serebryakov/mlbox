from __future__ import absolute_import, division, print_function, unicode_literals
import yaml
import os
import argparse
import logging
import logging.config
from typing import List, Union
import tensorflow as tf


logger = logging.getLogger(__name__)


def train(task_args: List[str], log_dir: str, data_dir: Union[None, str] = None) -> None:
    """ Task: train.
    Input parameters:
        --data_dir, --log_dir, --model_dir, --parameters_file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--parameters_file', '--parameters-file', type=str, default=None,
                        help="Parameters default values.")
    args = parser.parse_args(args=task_args)

    with open(args.parameters_file, 'r') as stream:
        parameters = yaml.load(stream, Loader=yaml.FullLoader)
    logger.info("Parameters have been read (%s).", args.parameters_file)

    # Grab all GPUs
    num_workers = len(tf.config.experimental.list_physical_devices('GPU'))
    if num_workers == 0:
        num_workers = 1
    # TODO: https://github.com/mlperf/training_results_v0.6/blob/master/NVIDIA/benchmarks/resnet/implementations/mxnet/ompi_bind_DGX1.sh
    cmd = "mpiexec --allow-run-as-root --bind-to none -np {} python ./{}.py {}".format(
        num_workers,
        parameters.pop('model'),
        ' '.join(["--{}={}".format(param, value) for param, value in parameters.items()])
    )
    if data_dir is not None:
        cmd = "{} --log_dir={} --data_dir={}".format(cmd, log_dir, data_dir)
    print(cmd)
    logger.info("Command: %s", cmd)

    if os.system(cmd) != 0:
        raise RuntimeError('Command failed: {}'.format(cmd))


def main():
    """
    mnist.py task task_specific_parameters...
    """
    # noinspection PyBroadException
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--mlbox_task', '--mlbox-task', type=str, required=True,
                            help="Task for this MLBOX.")
        parser.add_argument('--log_dir', '--log-dir', type=str, required=True,
                            help="Logging directory.")
        parser.add_argument('--data_dir', '--data-dir', type=str, required=False, default=None,
                            help="Dataset directory.")
        ml_box_args, task_args = parser.parse_known_args()

        logger_config = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {"format": "%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s"},
            },
            "handlers": {
                "file_handler": {
                    "class": "logging.FileHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": os.path.join(ml_box_args.log_dir, "mlbox_ngc_tf_{}.log".format(ml_box_args.mlbox_task))
                }
            },
            "loggers": {
                "": {"level": "INFO", "handlers": ["file_handler"]},
                "__main__": {"level": "NOTSET", "propagate": "yes"},
                "tensorflow": {"level": "NOTSET", "propagate": "yes"}
            }
        }
        logging.config.dictConfig(logger_config)

        if ml_box_args.mlbox_task == 'benchmark':
            train(task_args, log_dir=ml_box_args.log_dir, data_dir=ml_box_args.data_dir)
        else:
            raise ValueError("Unknown task: {}".format(ml_box_args.mlbox_task))
    except Exception as err:
        logger.exception(err)


if __name__ == '__main__':
    main()
