#!/bin/bash
  
#docker image rm dune_image

#docker build --file ./Dockerfile -t dune_image .
docker build --file ./Dockerfile -t dune_image . --no-cache
