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

```shell script
# Build docker image
python3 -m mlbox configure ./examples/ngc/tensorflow

# One 8-GPU training session, no memory limits.
mkdir ./examples/ngc/tensorflow/workspace/log_lustre_nvme_nvidia_8_0_all
python3 -m mlbox run ./examples/ngc/docker.platforms.yaml:nvidia_8_0_all ./examples/ngc/tensorflow:benchmark/imagenet --log_dir=log_lustre_nvme_nvidia_8_0_all >> ./examples/ngc/tensorflow/workspace/log_lustre_nvme_nvidia_8_0_all/mlbox.log 2>&1

# One 8-GPU training session, max container memory 224G memory.
mkdir ./examples/ngc/tensorflow/workspace/log_lustre_nvme_nvidia_8_0_224g
python3 -m mlbox run ./examples/ngc/docker.platforms.yaml:nvidia_8_0_224g ./examples/ngc/tensorflow:benchmark/imagenet --log_dir=log_lustre_nvme_nvidia_8_0_224g >> ./examples/ngc/tensorflow/workspace/log_lustre_nvme_nvidia_8_0_224g/mlbox.log 2>&1 

# One 8-GPU training session, max container memory 256G memory.
mkdir ./examples/ngc/tensorflow/workspace/log_lustre_nvme_nvidia_8_0_256g
python3 -m mlbox run ./examples/ngc/docker.platforms.yaml:nvidia_8_0_256g ./examples/ngc/tensorflow:benchmark/imagenet --log_dir=log_lustre_nvme_nvidia_8_0_256g >> ./examples/ngc/tensorflow/workspace/log_lustre_nvme_nvidia_8_0_256g/mlbox.log 2>&1
```

