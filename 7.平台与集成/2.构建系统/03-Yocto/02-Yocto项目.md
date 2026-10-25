---
id: "build-02"
title: 1. 启动第一个Yocto项目构建
cluster: build
layer: L4
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["build", "yocto"]
aliases: ["Yocto项目"]
created: 2026-10-24
updated: 2026-10-24
---
# 1. 启动第一个Yocto项目构建

## 1.1. 设置构建主机
Ubuntu

```
sudo apt-get install gawk wget git-core diffstat unzip texinfo gcc-multilib build-essential chrpath socat libsdl1.2-dev xterm
```

## 1.2. 安装Poky
下载Poky发布版本
https://www.yoctoproject.org/downloads

```
mkdir yocto
cd Yocto
tar xvfj poky-<codename>-release.tar.bz2
```

## 1.3. 配置构建环境
```
source <pokypath>/oe-init-build-env <builddir>
```
### 1.3.1. 构建环境的主要配置文件
conf/local.conf
![local.conf](assets/p-02-local.conf.jpg)

## 1.4. 编译构建
```
bitbake core-image-sato
```
