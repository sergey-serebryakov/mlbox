# Creating MNIST MLBox from scratch

This document briefly describes the process of creating an MLBox using as an example simple MNIST training workload.

> Several MNIST MLBoxes are implemented [here](../examples/mnist).

## MLBox definition file
We start by designing MLBox [definition file](../examples/mnist/docker/mlbox.yaml). The purpose of this file is to
mark a directory as a MLBox root directory. It contains metadata as well as definitions of MLBox capabilities at a 
very high level:
```yaml
type: mlbox
mlbox_spec_version: 0.1
name: MNIST
version: 0.1
author: MLPerf Best Practices Working Group
implementation: docker
tasks:
  downloaddata:
    inputs: {}
    outputs:
      data_dir:
        description: "A directory where MNIST dataset is downloaded."
      log_dir:
        description: "Directory for MLPerf log files."
  train:
    inputs:
      data_dir:
        description: "Input MNIST data set downloaded by the 'downloaddata' task."
      parameters_file:
        description: "Default values for the MNIST training implementation."
    outputs:
      log_dir:
        description: "Directory for MLPerf log files."
      model_dir:
        description: "Directory to save MNIST model training checkpoints."
```
The `type`, `mlbox_spec_version`, `name`, `version` and `author` are self-explanatory fields. The `implementation`
field defines how this MLBox is implemented. In this particular case, it is docker-based and users need to use
special docker runner to run this MLBox.

> Other possible MLBox implementation types are, for example, `python` (bare metal python implementation) and
> `singularity`.

The `tasks` field defines tasks this MLBox supports.

> A task is a well-defined functionality implemented by a MLBox. Typical examples are data download, data
> pre-processing, training, testing, generating reports etc.

In the MLBox definition file we need to define tasks and their parameters.

> By definition (currently) every task parameter is either a directory or a file - in other words, a file system
> artifact. Parameters such as batch size, learning rate schedule etc. are stored in files. MLBox distinguishes between
> input parameters and output parameters (we need to clearly communicate why we distinguish between them). 

> Every task parameter will eventually become an argument of an implementation script (will be described below).

In the MNIST MLBox we will support two tasks - `downloaddata` and `train`:
- `downloaddata` task downloads MNIST data set. This task does not have any input parameters (the URL is hard coded).
  So, its `inputs` section is empty. This tasks produces two outputs. Obviously, a data set that is located in a 
  directory specified by the `data_dir` parameter. The second output is the log file located in the directory
  specified by the `log_dir` parameter.

> We mentioned above that task parameters will become implementation script arguments. So, something like this
> will occur: `implementation_script.py ... --data_dir=DATA_DIR --log_dir=LOG_DIR ...`

- `train` task trains an MNIST model. It requires two input and two output parameters. Input parameters are directories
  containing downloaded data set `data_dir` and configuration file with parameters (`parameters_file`) that
  defines hyper-parameters for training MNIST model. Two output parameters are `log_dir` that will contain log records
  of a training session and `model_dir` directory containing artifacts such as model snapshots, TensorFlow log files,
  TensorBoard files etc.

So, the purpose of the MLBox definition file is to give an overview of MLBox capabilities. 

## Workspace
The [workspace](../examples/mnist/docker/workspace) is the default place for MLBox input/output artifacts.

> It will be described below, but all relative paths in the MLBox configuration files are relative to this workspace
> directory. Absolute paths are treated as absolute paths and can point to any location.

Users are free to use any directory structure for the MLBox workspace. In the MNIST MLBox the workspace contains:
- [data](../examples/mnist/docker/workspace/data) directory containing MNIST dataset.
- [log](../examples/mnist/docker/workspace/log) directory containing tasks' log files.
- [model](../examples/mnist/docker/workspace/model) directory containing output artifacts of the `train` task.
- [parameters](../examples/mnist/docker/workspace/parameters) directory containing hyper-parameters for the MNIST model.

The hyper-parameters [configuration file](../examples/mnist/docker/workspace/parameters/default.parameters.yaml)
contains a small number of parameters such as optimizer, number of training epochs and replica batch size:
```yaml
optimizer: "adam"
train_epochs: 5
batch_size: 32
```
Contents of files like this one is application specific. MLBox will pass the file system path to this file
to the implementation script and it is MLBox developer responsibility to load parameters.

> If MLBox is a docker-based implementation, MLBox runners will translate host paths to internal docker paths and will
> mount respective directories. Developers in their implementation scrips need to assume that MLBox runners will take
> all necessary actions to ensure the configuration and other files are readable/writable by implementation scripts.

## Tasks
The next step is to create a definition of each task. The goal is basically to assign values to task parameters listed
in the mlbox [definition file](../examples/mnist/docker/mlbox.yaml).

Tasks are defined in [tasks](../examples/mnist/docker/tasks) directory. Each task is defined in its own sub-directory:
[downloaddata](../examples/mnist/docker/tasks/downloaddata) for `downloaddata` task and
[train](../examples/mnist/docker/tasks/train) for the `train` task.

Task parameters are defined in task definition files. One task may have multiple definition files, and users can
specify which parameters they want to use when running MLBoxes. The idea is, for instance, to be able to train small
and large variants of models, or use different hyper-parameters for 4-way and 8-way GPU servers for faster
convergence.

> Task definition files named as `default.yaml` contain default parameters that are used if a user does not specify
> what they want to use on a command line (will be described below).

- [downloaddata](../examples/mnist/docker/tasks/downloaddata/default.yaml) default task file assigns values to two
  task parameters - `data_dir` and `log_dir`:
  ```yaml
  data_dir: data
  log_dir: log
  ```
  Since every parameter is a file system path, and paths in this file are relative (`data` and `log`), they are
  considered to be relative to a MLBox workspace directory ([data](../examples/mnist/docker/workspace/data) and
  [log](../examples/mnist/docker/workspace/log)).
- [train](../examples/mnist/docker/tasks/downloaddata/default.yaml) default task file assigns parameters in a similar
  way:
  ```yaml
  parameters_file: parameters/default.parameters.yaml
  data_dir: data
  log_dir: log
  model_dir: model
  ```
  Here, all file system paths are relative, and so, they are relative with respect to the
  [workspace](../examples/mnist/docker/workspace) root directory.

## Implementation
Finally, we need to implement the MNIST training workload. In general, users are free to implement in whatever way
they think it makes more sense taking into account how they plan to run it - bare metal, python or singularity.

Here, we will be implementing a MNIST training process as docker container. Currently, the docker runner assumes that
docker image defines an entry point that points to a run script. So, docker runner just runs the container and passes
all task parameters on a command line. Docker runner assumes that Dockerfile is locate in
[docker/dockerfiles](../examples/mnist/docker/implementation/docker/dockerfiles) directory that's relative to
the [implementation](../examples/mnist/docker/implementation) folder.

Developers need to follow two mandatory rules:
- They need to define an entry point in their dockerfile that must accept parameters.
- Developers need to assume that the context directory for building docker image will be the MLBox root
  directory, so, all paths (for instance, for `COPY` commands) needs to be relative to MLBox root directory and
  must point to files inside the MLBox directory.   
 
In this particular example, the docker file looks like this:
```shell script
# Define the base OS and image tags
FROM ubuntu:18.04
MAINTAINER MLPerf MLBox Working Group

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            software-properties-common \
            python3-dev \
            curl && \
    rm -rf /var/lib/apt/lists/*

# Install pip
RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

# Copy MNIST training implementation script and install its python dependencies.
# Use relative paths that are relative to the MLBox root directory!
COPY implementation/src/requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

# Make sure entry point is defined!
COPY implementation/src/mnist.py /workspace/mnist.py
ENTRYPOINT ["python3", "/workspace/mnist.py"]
```

The implementation script and its dependencies are located in the
[src](../examples/mnist/docker/implementation/src) directory. When implementing scripts, developers must
follow these rules:
- An mlbox runner will pass a task name using `--mlbox_task` command line argument. In the case of MNIST MLBox, it will
  be one of: `--mlbox_task=downloaddata` or `--mlbox_task=train`.
- Developers must parse task specific parameters they define in mlbox and task definition files.
  - For the `downloaddata` task, it will be `--log_dir` and `--data_dir`.
  - For the `train` task, it will be `--log_dir`, `--data_dir`, `--model_dir` and `--parameters_file`.

Developers also need to provide [mlbox implementation](../examples/mnist/docker/implementation/mlbox_implementation.yaml)
file. That's mlbox implementation specific, and for the docker-based implementations it needs to contain the following
mandatory parameters:
```yaml
# Again, specify implementation type
implementation_type: docker
# Must provide image name
image: mlperf/mlbox-example-mnist
# This is probably not required, since latest docker supports nvidia natively.
docker_runtime: nvidia-docker # OR docker
# What to do at the configure phase (see below) - 'build' or 'pull'
configure: build # OR pull
```
It's still under the development, so these parameters will change.

## Platform definition files
Users can also have platform definition files that describe runtime parameters and requirements. Contents of these
files depend on a particular runner (docker/python/ssh/k8s/cloud) and their description is out of scope of this
short introduction. 

## Running
MLBox runners provide commands to configure and run MLBoxes. In addition, they can provide other functionality. In 
general, every MLBox runner must support at least two commands:
- `configure` that must configure local or remote node. If done, it is guaranteed that MLBox can run (assuming
  input artifacts are present). At this phase, for instance, docker runner builds or pulls images.
- `run` that runs a particular task.

> Before running the commands below, make sure you use python >= 3.5 and have docker installed.

```shell script
# Briefly describe what's inside MLBox
python -m mlbox describe ./examples/mnist/docker

# Configure MNIST MLBox (export proxy servers if behind a corporate firewall)
https_proxy=${http_proxy} python -m mlbox configure ./examples/mnist/docker

# Run `downloaddata` task with default set of parameters
python -m mlbox run ./examples/mnist/docker:downloaddata

# Run `train` task with default set of parameters
python -m mlbox run ./examples/mnist/docker:train
```

These are equivalent commands to run MNIST tasks when users can specify that they want to use default sets of
parameters:
```shell script
# Run `downloaddata` task with default set of parameters
python -m mlbox run ./examples/mnist/docker:downloaddata/default

# Run `train` task with default set of parameters
python -m mlbox run ./examples/mnist/docker:train/default
```

## Other MLBoxes
The [examples](../examples) directory contains this and other MLBoxes. In particular, in addition to docker-based
[MNIST implementation](../examples/mnist/docker) it provides [bare metal](../examples/mnist/baremetal) and
[singularity](../examples/mnist/singularity)-based implementations.
