# NVIDIA GPU Cloud (NGC) MLBoxes

Configure MLBox (build docker image).
```shell script
python -m mlbox configure ./examples/ngc/tensorflow
```

Run benchmarks with synthetic data (no ImageNet data set is required).
```shell script
python -m mlbox run ./examples/ngc/docker.platforms.yaml:nvidia_1 ./examples/ngc/tensorflow:benchmark/synthetic
```

When running benchmarks with real data set (ImageNet), clean the `ngc/tensorflow/workspace/log` directory before each
run. Update the [imagenet.yaml](./tensorflow/tasks/benchmark/imagenet.yaml) and specify path to your ImageNet data set
(`data_dir`) parameter. The data set should be the standard TensorFlow (*.tfrecord) data set.
```shell script
rm  ./examples/ngc/tensorflow/workspace/log/*
python -m mlbox run ./examples/ngc/docker.platforms.yaml:nvidia_1 ./examples/ngc/tensorflow:benchmark/imagenet
```
The platform definition file contains several sections for different number of GPUs - nvidia_1, nvidia_2, nvidia_4 and
nvidia_8. No process pinning is used.
