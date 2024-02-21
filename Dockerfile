FROM python:3.8

# install python packages and dunetoolkit
COPY . /home/Radiopurity-database-assistant/
WORKDIR /home/Radiopurity-database-assistant/

# Python dependencies
RUN pip install -r ./user_interface/requirements.txt 
RUN pip install -e .

# build documentation and create symbolic link to UI static dir so HTML docs can be hosted on UI
WORKDIR /home/Radiopurity-database-assistant/docs 
RUN make clean && make html && ln -s /home/Radiopurity-database-assistant/docs/build/html /home/Radiopurity-database-assistant/user_interface/static/docs

# default command
WORKDIR /home/Radiopurity-database-assistant/user_interface
ENTRYPOINT ./run.sh

