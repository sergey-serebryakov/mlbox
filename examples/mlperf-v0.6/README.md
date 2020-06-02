# MLPerf Training Benchmarks V-0.6

## NVIDIA ResNet
```shell script
python3.6 -m mlbox describe ./examples/mlperf-v0.6/nvidia-resnet
python3.6 -m mlbox configure ./examples/mlperf-v0.6/nvidia-resnet
python3.6 -m mlbox run ./examples/mlperf-v0.6/nvidia-resnet:benchmark
```


## NVIDIA SSD
```shell script
python3.6 -m mlbox describe ./examples/mlperf-v0.6/nvidia-ssd
python3.6 -m mlbox configure ./examples/mlperf-v0.6/nvidia-ssd
python3.6 -m mlbox run ./examples/mlperf-v0.6/nvidia-ssd:benchmark
```

## NVIDIA MaskRCNN
```shell script
python3.6 -m mlbox describe ./examples/mlperf-v0.6/nvidia-maskrcnn
python3.6 -m mlbox configure ./examples/mlperf-v0.6/nvidia-maskrcnn
python3.6 -m mlbox run ./examples/mlperf-v0.6/nvidia-maskrcnn:benchmark
```
