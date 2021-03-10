FROM ubuntu:16.04

# install python3.6
RUN apt-get update && apt-get install -y \
  software-properties-common build-essential git

RUN add-apt-repository ppa:deadsnakes/ppa 
RUN apt-get update && apt-get install -y \
  python3.6 python3.6-dev python3-pip python3.6-venv && \
  apt-get update && \
  apt-get clean && \
  apt-get autoremove

# clone git repo
WORKDIR /home/
RUN git clone https://github.com/pnnl/Radiopurity-database-assistant.git

# install python packages and dunetoolkit
RUN cd /home/Radiopurity-database-assistant && python3 setup.py install
RUN cd /home/Radiopurity-database-assistant && pip3 install -r user_interface/requirements.txt
WORKDIR /home/Radiopurity-database-assistant/user_interface

# build documentation and create symbolic link to UI static dir so HTML docs can be hosted on UI
RUN cd /home/Radiopurity-database-assistant/docs && make clean && make html && \
  ln -s /home/Radiopurity-database-assistant/docs/build/html /home/Radiopurity-database-assistant/user_interface/static/docs

# for running and testing the flask app
COPY ./user_interface/app_config_docker.json /home/Radiopurity-database-assistant/user_interface/app_config.json
COPY ./user_interface/app_config_docker_test.json /home/Radiopurity-database-assistant/user_interface/app_config_test.json

# default command
ENTRYPOINT ./run.sh

