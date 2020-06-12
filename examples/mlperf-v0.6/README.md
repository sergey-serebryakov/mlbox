# MLPerf Training Benchmarks V-0.6


## Benchmarks
Clone prototype implementation of a MLBox runners and example MLBoxes including those implementing benchmarks.
```shell script
git clone https://github.com/sergey-serebryakov/mlbox.git
cd ./mlbox && git checkout feature/mlbox_runners_v2
```

## MLPerf/NVIDIA/ResNet:LocalVolume
Examples in this section assume data (ImageNet in MXNET format) is located in `/lvol/serebrya/datasets/imagenet_mxnet`
(see step #3) - adjust to your location.
- Step 1
  ```shell script
  export mlbox=examples/mlperf-v0.6/nvidia-resnet
  python3 -m mlbox configure ${mlbox}
  ```

- Step 2
  For each command here, execute step #3
  ```shell script
  export memory=unlim data=lvol
  export memory=128g data=lvol
  ```

- Step 3
  ```shell script
  export user_args="--parameters_file=parameters/${memory}_memory.yaml --data_dir=/lvol/serebrya/datasets/imagenet_mxnet --log_dir=${memory}_${data}"
  mkdir ${mlbox}/workspace/${memory}_${data}
  python3 -m mlbox run ${mlbox}:benchmark ${user_args} >> ${mlbox}/workspace/${memory}_${data}/mlbox.log 2>&1
  ```

### MLPerf/NVIDIA/SSD:LocalVolume
Examples in this section assume data (COCO data set) is located in `/lvol/serebrya/datasets/coco`
(see step #3) - adjust to your location.

- Step 1
  ```shell script
  export mlbox=examples/mlperf-v0.6/nvidia-ssd
  python3 -m mlbox configure ${mlbox}
  ```

- Step 2
  For each command here, execute step #3
  ```shell script
  export memory=unlim data=lvol
  export memory=128g data=lvol
  export memory=64g data=lvol
  export memory=32g data=lvol
  ```

- Step 3
  ```shell script
  export user_args="--parameters_file=parameters/${memory}_memory.yaml --data_dir=/lvol/serebrya/datasets/coco --log_dir=${memory}_${data}"
  mkdir ${mlbox}/workspace/${memory}_${data}
  python3 -m mlbox run ${mlbox}:benchmark ${user_args} >> ${mlbox}/workspace/${memory}_${data}/mlbox.log 2>&1
  ```

## NGC/TensorFlow/ResNet:LocalVolume
Examples in this section assume data (ImageNet in TensorFlow format) is located in `/lvol/serebrya/datasets/imagenet_tensorflow `
(see step #3) - adjust to your location.
- Step 1
  ```shell script
  export mlbox=examples/ngc/tensorflow
  python3 -m mlbox configure ${mlbox}
  ```

- Step 2
  For each command here, execute step #3
  ```shell script
  export memory=unlim data=lvol
  ```

- Step 3
  ```shell script
  export user_args="--data_dir=/lvol/serebrya/datasets/imagenet_tensorflow --log_dir=${memory}_${data}"
  mkdir ${mlbox}/workspace/${memory}_${data}
  python3 -m mlbox run examples/ngc/docker.platforms.yaml:nvidia_8_0_all ${mlbox}:benchmark/imagenet ${user_args} >> ${mlbox}/workspace/${memory}_${data}/mlbox.log 2>&1
  ```

## NGC/TensorFlow/ResNet:Lustre (ssd|hdd|nvme)
Examples in this section assume data (ImageNet in TensorFlow format) is located in `/lustre/${data}/datasets/imagenet_tensorflow`
(see step #3) - adjust to your location.

- Step 1
  ```shell script
  export mlbox=examples/ngc/tensorflow
  python3 -m mlbox configure ${mlbox}
  ```

- Step 2
  For each command here, execute step #3
  ```shell script
  export memory=unlim data=nvme
  export memory=unlim data=ssd
  export memory=unlim data=hdd
  ```

- Step 3
  ```shell script
  export user_args="--data_dir=/lustre/${data}/datasets/imagenet_tensorflow --log_dir=${memory}_lustre_${data}"
  mkdir ${mlbox}/workspace/${memory}_lustre_${data}
  python3 -m mlbox run examples/ngc/docker.platforms.yaml:nvidia_8_0_all ${mlbox}:benchmark/imagenet ${user_args} >> ${mlbox}/workspace/${memory}_lustre_${data}/mlbox.log 2>&1
  ```
