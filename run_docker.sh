#!/bin/bash

if [ "$1" = "test" ]; then
    echo "Running app tests"
    docker run -d --expose 27017 -p 5000:5000 -p 27017:27017 --entrypoint ./run_test.sh dune_image
else
    echo "Running app"
    docker run -d --expose 27017 -p 5000:5000 -p 27017:27017 dune_image
fi

