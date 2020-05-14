FROM ubuntu:18.04

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            software-properties-common\
            numactl \
            build-essential \
            cpio \
            curl \
            wget \
            git \
            lsb-release \
            pciutils \
            python3-dev \
            sudo \
            mc \
            vim && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fSsL -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

RUN wget http://registrationcenter-download.intel.com/akdlm/irc_nas/15792/l_openvino_toolkit_p_2019.2.275.tgz && \
    tar -xf l_openvino_toolkit_p_2019.2.275.tgz && \
    mv l_openvino_toolkit_p_2019.2.275  /openvino && \
    rm -r l_openvino_toolkit_p_2019.2.275.tgz

ARG OPENVINO_DIR=/opt/intel/openvino
# OpenVINO dependencies
RUN cd /openvino/ && ./install_openvino_dependencies.sh

RUN pip3 install wheel numpy pyyaml

# OpenVINO itself
RUN cd /openvino/ && \
    sed -i 's/decline/accept/g' silent.cfg && \
    ./install.sh --silent silent.cfg

# Model Optimizer
RUN cd ${OPENVINO_DIR}/deployment_tools/model_optimizer/install_prerequisites && \
    ./install_prerequisites.sh

# Model ZOO
RUN cd ${OPENVINO_DIR}/deployment_tools/open_model_zoo/tools/downloader && \
    pip3 install -r ./requirements.in

# Benchmark APP (SHELL thing: https://stackoverflow.com/a/25423366)
SHELL ["/bin/bash", "-c"]
RUN mkdir /opt/intel/openvino_benchmark_app && \
    cd /opt/intel/openvino_benchmark_app && \
    source ${OPENVINO_DIR}/bin/setupvars.sh && \
    cmake -DCMAKE_BUILD_TYPE=Release ${OPENVINO_DIR}/deployment_tools/inference_engine/samples && \
    make -j"$(nproc)" benchmark_app
SHELL ["/bin/sh", "-c"]

# Clean up
RUN apt autoremove -y && \
    rm -rf /openvino /var/lib/apt/lists/*

ENV OPENVINO_DIR=${OPENVINO_DIR}

# For interactive shells (docker run -i ...).
RUN echo "source ${OPENVINO_DIR}/bin/setupvars.sh" >> /root/.bashrc

RUN git clone https://github.com/HewlettPackard/dlcookbook-dlbs.git /dlbs

# COPY implementation/src/entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh
# ENTRYPOINT ["/entrypoint.sh"]

COPY implementation/src/entrypoint.py /entrypoint.py
COPY implementation/src/openvino.sh /dlbs/scripts/launchers/openvino.sh
COPY implementation/src/openvino.json /dlbs/python/dlbs/configs/openvino.json
ENTRYPOINT ["python3", "/entrypoint.py"]