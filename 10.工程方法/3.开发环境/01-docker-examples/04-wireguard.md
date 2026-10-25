---
id: "env-04"
title: description
cluster: env
layer: L1
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["wireguard", "docker"]
aliases: ["wireguard"]
created: 2026-10-24
updated: 2026-10-24
---
# description


# build docker image
```SHELL
# docker image name: ubuntu-server, tag:wireguard
docker build -t ubuntu-server:wireguard .
```

# docker network
```SHELL
docker network create --driver macvlan --subnet=192.168.88.0/24 --gateway=192.168.88.1 -o parent=ens38 net88
```

# run docker container
```SHELL
# $PWD is source code root dir
docker run --name WIREGUARD-SERVER --cap-add=NET_ADMIN --network=net88 --ip 192.168.88.52 -v $PWD/wireguard:/etc/wireguard/ -v /etc/localtime:/etc/localtime -w /root/ -i -t -d ubuntu-server:wireguard /bin/bash
```

# rerun container
```SHELL
# get docker container info id
docker ps -a 
# rerun docker container with id
docker exec -it 9df70f9a0714 /bin/bash 
```
