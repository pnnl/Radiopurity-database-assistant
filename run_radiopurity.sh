#!/bin/sh

openssl req -x509 -nodes -newkey rsa:2048 -keyout key.pem -out cert.pem -sha256 -days 365 \
    -subj "/C=GB/ST=Seattle/L=Seattle/O=PNNL/OU=SEA Department/CN=localhost"

docker-compose up --build -d