# FROM nvcr.io/nvidia/tensorflow:18.07-py3
FROM nvcr.io/nvidia/tensorflow:20.03-tf2-py3
MAINTAINER MLPerf MLBox Working Group

# Remove all stopped containers: docker rm $(docker ps -a -q)
# Remove containers like none:none: docker rmi $(docker images | grep none | awk '{print $3}')


COPY implementation/src/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY implementation/src/mlbox_runner.py /workspace/nvidia-examples/cnn/mlbox_runner.py

# Add time stamp to the output
RUN sed -i '52s/.*/        print("time_stamp: %f, global_step: %d images_per_sec: %.1f" % (timestamp, self.global_steps,/' /workspace/nvidia-examples/cnn/nvutils/runner.py

WORKDIR /workspace/nvidia-examples/cnn
ENTRYPOINT ["python", "mlbox_runner.py"]
