---
id: "env-01"
title: "docker"
cluster: env
layer: L1
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["docker"]
aliases: ["docker"]
created: 2026-10-24
updated: 2026-10-24
---
# docker


## build docker image


```SHELL
# docker image name: ubuntu-server, tag:wireguard
docker build -t ubuntu-server:wireguard .
```

## docker network
```SHELL
docker network create --driver macvlan --subnet=192.168.88.0/24 --gateway=192.168.88.1 -o parent=ens38 net88
```

## run docker container
```SHELL
# $PWD is source code root dir
docker run --name WIREGUARD-SERVER --cap-add=NET_ADMIN --network=net88 --ip 192.168.88.52 -v $PWD/wireguard:/etc/wireguard/ -v /etc/localtime:/etc/localtime -w /root/ -i -t -d ubuntu-server:wireguard /bin/bash
```

## rerun container
```SHELL
# get docker container info id
docker ps -a 
# rerun docker container with id
docker exec -it 9df70f9a0714 /bin/bash 
```

## 运行


### 查看镜像
```SHELL
docker images
```

### 查看所有容器
```SHELL
docker ps -a
```

### 创建容器
```SHELL
docker run --name T750-COMPILER -v $PWD:/root/workspack/ -v /etc/localtime:/etc/localtime -w /root/workspack/ -i -t -d  ubuntu-compiler:T750 /bin/bash
```

### 启动已停止的容器
```SHELL
docker start b51658521542
```

### 进入容器
```SHELL
docker exec -it b51658521542 /bin/bash
```
