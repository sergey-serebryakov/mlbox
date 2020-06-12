```shell script

python3.6 -m mlbox configure ./examples/mlperf-v0.6/nvidia-resnet

export drives=nvme
export mem=all
export mem=128g

mkdir ./examples/mlperf-v0.6/nvidia-resnet/workspace/log_lustre_${drives}_nvidia_8_0_${mem}
python3 -m mlbox run ./examples/ngc/docker.platforms.yaml:nvidia_8_0_${mem} ./examples/mlperf-v0.6/nvidia-resnet:benchmark --log_dir=log_lustre_${drives}_nvidia_8_0_${mem} >> ./examples/mlperf-v0.6/nvidia-resnet/workspace/log_lustre_${drives}_nvidia_8_0_${mem}/mlbox.log 2>&1


```