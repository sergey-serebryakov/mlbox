# MLBox


```shell script
virtualenv -p python3.6 ./.virtualenv-3.6
source ./.virtualenv-3.6/bin/activate
pip install pyaml
```

```shell script
python -m mlbox
python -m mlbox help describe
python -m mlbox help configure
python -m mlbox help run
```
> Docker runner uses `http_proxy`/`https_proxy` environmental variables during configure/run phases.

> Singularity runner stores images in `implementation/singularity/recipes` MLBox directory.

> Singularity version needs to be >= 3.5

## Hello World: bare metal, docker, singularity
Docker/Singularity base image is Ubuntu:18.04
```shell script
# Bare metal
python -m mlbox describe ./examples/hello_world/baremetal
python -m mlbox configure ./examples/hello_world/baremetal
python -m mlbox run ./examples/hello_world/baremetal:hello/xinyuan
python -m mlbox run ./examples/hello_world/baremetal:goodbye/xinyuan

# Docker containers
python -m mlbox describe ./examples/hello_world/docker
https_proxy=${http_proxy} python -m mlbox configure ./examples/hello_world/docker
python -m mlbox run ./examples/hello_world/docker:hello/xinyuan
python -m mlbox run ./examples/hello_world/docker:goodbye/xinyuan

# Singularity containers
python -m mlbox describe ./examples/hello_world/singularity
https_proxy=${http_proxy} python -m mlbox configure ./examples/hello_world/singularity
python -m mlbox run ./examples/hello_world/singularity:hello/xinyuan
python -m mlbox run ./examples/hello_world/singularity:goodbye/xinyuan
```

## MNIST: bare metal, docker, singularity
Docker/Singularity base image is Ubuntu:18.04
```shell script
# Bare metal
python -m mlbox describe ./examples/mnist/baremetal
python -m mlbox configure ./examples/mnist/baremetal
python -m mlbox run ./examples/mnist/baremetal:downloaddata
python -m mlbox run ./examples/mnist/baremetal:train

# Docker containers
python -m mlbox describe ./examples/mnist/docker
https_proxy=${http_proxy} python -m mlbox configure ./examples/mnist/docker
python -m mlbox run ./examples/mnist/docker:downloaddata
python -m mlbox run ./examples/mnist/docker:train

# Singularity containers
python -m mlbox describe ./examples/mnist/singularity
https_proxy=${http_proxy} python -m mlbox configure ./examples/mnist/singularity
python -m mlbox run ./examples/mnist/singularity:downloaddata
python -m mlbox run ./examples/mnist/singularity:train
```

## NGC TensorFlow
```shell script
python -m mlbox describe ./examples/ngc/tensorflow
# Configure MLBox (build docker container)
python -m mlbox configure ./examples/ngc/tensorflow
# Run a small benchmark using all available GPU devices
python -m mlbox run ./examples/ngc/tensorflow:benchmark/test
# Run 500 iterations using synthetic data, mixed precision and all available GPU devices
python -m mlbox run ./examples/ngc/tensorflow:benchmark/synthetic
# Run 500 iterations using ImageNet data, mixed precision and all available GPU devices
# ImageNet datasets (tfrecords) must be mounted to workspace/data
python -m mlbox run ./examples/ngc/tensorflow:benchmark/imagenet
```

## DLBS - OpenVino: docker
```shell script
https_proxy=${http_proxy} python -m mlbox configure ./examples/dlbs/openvino
python -m mlbox run ./examples/dlbs/openvino:validate
python -m mlbox run ./examples/dlbs/openvino:run
python -m mlbox run ./examples/dlbs/openvino:report
```

## Notes

1. How do users know in what order they need to run tasks? Several blog posts propose to use makefiles where
   targets can naturally depend on other targets.
2. Will be convenient to support multiple implementations in one MLBox (bare metal, docker, singularity etc.).
3. Creating an MLBox from scratch is not straightforward. Probably OK for ML performance engineers, but not for data
   scientists / researchers.
4. How to deal with python-based bare metal MLBoxes? Should implementation file require a certain python
   environment such as virtualenv or conda? For instance, on my (Sergey) laptop I use Anaconda, but on other
   servers I use virtualenv. It seems there are no such issues with containers. Or we can just stick to a
   virtualenv/conda that's part of MLBox source tree. Or we can try to automatically identify what's available
   and use that.
5. What's the right location for large MLBox artifacts such as python virtual environments with tens or
   hundreds packages or Singularity containers?
6. Dockerfiles/singularity recipes seem to share a lot between different projects. MLBox can provide templates.
7. Probably, need to clean output directories before running tasks.
8. Docker runner uses docker runtime in cases when MLBoxes list nvidia-docker as a requirement, and nvidia-docker
   is not installed.



## Running on a remote host

> I needed to update .bashrc on my remote hosts to set proxy variables in cases when ssh is executed with a command.

> I did not test running singularity containers on remote hosts.

The `platforms/platforms.yaml` file has the following content:
```yaml
# To have multiple platforms in one configuration file, each platform is defined under its own name.
aiops1:
  # This section configures a SSHRunner for a particular platform, in this case, a particular remote mode. The
  # 'runner' key below overrides standard mapping between a MLBox implementation_type and runner type i.e. for MLBox
  # of docker type it says do not use docker runner, instead, use SSH runner and run MLBox on a remote host with
  # docker runner.
  runner: ssh
  # In current implementation, we need host and user.
  host: HOST_NAME
  user: USER_NAME
  # MLBox package: remote location and if it needs to be synced with local directory. Temporary solution. Better way
  # to install it is like `pip install ...`. If remote_dir is None or 'runtime' key is not present, assume:
  # runtime = {remote_dir: ".mlbox", sync: "true"} i.e. use ${HOME}/.mlbox
  # If remote_dir is not absolute, it is relative to a user home directory on a remote host.
  runtime:
    remote_dir: .mlbox
    sync: true
  # MLBox and its remote location and if it needs to be synced with local directory. This is unique for each
  # (MLBox, implementation) pair. For a particular node, this is the only configuration difference between different
  # MLBoxes. To keep it simple and have just one node configuration for any MLBox, SSHRunner assumes the following (if
  # remote_dir below is None or 'mlbox' section is not present):
  #   remote_dir = ${runtime.remote_dir}/mlboxes/${mlbox.name}/${mlbox.implementation_type}
  mlbox:
    remote_dir:
    sync: true

```

In current implementation, after a task has been completed, the whole MLBox directory will be copied back (rsync). The
difference from above examples is that here we need to provide a platform configuration file that overrides default
mapping between MLBox implementation type and a runner and instructs to use a different runner on a local host. 

## Hello World: bare metal, docker, singularity

```shell script
# Bare metal

# Configure MLBox on a remote host. 
python -m mlbox configure ./platforms/platforms.yaml:aiops1 ./examples/hello_world/baremetal
# Run task on a remote host and copy results back.
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/hello_world/baremetal:hello/xinyuan
# Run task on a remote host and copy results back.
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/hello_world/baremetal:goodbye/xinyuan


python -m mlbox configure ./platforms/platforms.yaml:aiops1 ./examples/hello_world/docker
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/hello_world/docker:hello/xinyuan
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/hello_world/docker:goodbye/xinyuan

python -m mlbox configure ./platforms/platforms.yaml:aiops1 ./examples/hello_world/singularity
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/hello_world/singularity:hello/xinyuan
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/hello_world/singularity:goodbye/xinyuan
```

## MNIST: bare metal, docker, singularity

> Syncing the whole MLBox directories may not be the best idea - virtual python environments and singularity containers
> are quire large.

```shell script
# Bare metal
python -m mlbox configure ./platforms/platforms.yaml:aiops1 ./examples/mnist/baremetal
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/mnist/baremetal:downloaddata
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/mnist/baremetal:train

# Docker containers
python -m mlbox configure ./platforms/platforms.yaml:aiops1 ./examples/mnist/docker
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/mnist/docker:downloaddata
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/mnist/docker:train

# Singularity containers
python -m mlbox configure ./platforms/platforms.yaml:aiops1 ./examples/mnist/singularity
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/mnist/singularity:downloaddata
python -m mlbox run ./platforms/platforms.yaml:aiops1 ./examples/mnist/singularity:train
```