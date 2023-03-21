FROM ubuntu:18.04

# install python3.8
RUN apt-get update && apt-get install -y \
  software-properties-common build-essential git curl

RUN add-apt-repository 'ppa:deadsnakes/ppa' 
RUN apt-get update && apt-get -y install \
  python3.8 python3.8-dev python3.8-venv && \
  apt-get update && \
  apt-get clean && \
  apt-get autoremove

# make python3.8 the default version for the python3 command
RUN rm -f /usr/bin/python3 && ln -s /usr/bin/python3.8 /usr/bin/python3

# Use a virtualenv - CREATE VENV BEFORE BUILDING - here we named it dune-venv
ENV VIRTUAL_ENV=/dune-venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set env for configs
ENV DUNE_API_CONFIG_NAME=/home/Radiopurity-database-assistant/user_interface/app_config_docker_test.json
ENV TOOLKIT_CONFIG_NAME=/home/Radiopurity-database-assistant/dunetoolkit/toolkit_config_docker_test.json

# install python packages and dunetoolkit
COPY . /home/Radiopurity-database-assistant/
WORKDIR /home/Radiopurity-database-assistant/

# Python dependencies
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.8 get-pip.py
RUN pip install -r ./user_interface/requirements.txt 
RUN pip install -e .

# build documentation and create symbolic link to UI static dir so HTML docs can be hosted on UI
WORKDIR /home/Radiopurity-database-assistant/docs 
RUN make clean && make html && ln -s /home/Radiopurity-database-assistant/docs/build/html /home/Radiopurity-database-assistant/user_interface/static/docs

# default command
WORKDIR /home/Radiopurity-database-assistant/user_interface
ENTRYPOINT ./run.sh

