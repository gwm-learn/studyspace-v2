---
id: "eng-build-01"
title: "make 与 CMake"
cluster: eng
layer: L2
status: draft
confidence: medium
platform: []
source:
  - type: doc
    ref: "GNU make manual; CMake documentation"
verified_on: null
tags: ["make", "cmake", "build", "cross-compile"]
aliases: ["Makefile", "CMake"]
created: 2026-10-24
updated: 2026-10-24
---

# make 与 CMake

> 解决什么问题：看懂/改 Makefile，写可维护的 CMake 工程，交叉编译不踩坑。
> 不解决：OpenWrt/Yocto 的包构建系统（见各自笔记）。

## 1. Makefile 基础

```make
CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra
TARGET = app
OBJS = main.o util.o

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: clean
```

| 符号 | 含义 |
|---|---|
| `$@` | 目标 |
| `$^` | 所有依赖 |
| `$<` | 第一个依赖 |
| `?=` | 未定义才赋值 |
| `:=` | 立即展开 |
| `=` | 延迟展开 |
| `.PHONY` | 伪目标 |

## 2. 常用函数

```make
SRCS := $(wildcard src/*.c)
OBJS := $(patsubst src/%.c,build/%.o,$(SRCS))
INC  := $(addprefix -I,$(INCDIRS))
```

| 函数 | 作用 |
|---|---|
| `wildcard` | 匹配文件 |
| `patsubst` | 模式替换 |
| `addprefix` | 加前缀 |
| `foreach` | 遍历 |
| `shell` | 执行命令（谨慎） |

## 3. 依赖与并行

- `make -j$(nproc)` 并行。
- 头文件依赖：`-MMD -MP` 生成 `.d` 并 `-include`。
- 增量构建：目标/依赖时间戳。
- 避免 `make` 递归滥用（`$(MAKE) -C` 可以）。

## 4. 交叉编译

```make
CROSS_COMPILE ?= aarch64-linux-gnu-
CC := $(CROSS_COMPILE)gcc
AR := $(CROSS_COMPILE)ar
STRIP := $(CROSS_COMPILE)strip

CFLAGS += --sysroot=$(SYSROOT)
LDFLAGS += --sysroot=$(SYSROOT)
```

要点：工具链/sysroot/ABI 一致；不要混用主机库。

## 5. CMake 基础

```cmake
cmake_minimum_required(VERSION 3.16)
project(app C)

set(CMAKE_C_STANDARD 11)
add_executable(app main.c util.c)
target_include_directories(app PRIVATE include)
target_compile_options(app PRIVATE -Wall -Wextra)
target_link_libraries(app PRIVATE m pthread)
```

| 命令 | 作用 |
|---|---|
| `add_library` | 库 |
| `target_*` | 目标级属性（推荐） |
| `find_package` | 找依赖 |
| `install` | 安装规则 |
| `configure_file` | 生成配置头 |

## 6. 交叉编译（CMake）

```bash
cmake -S . -B build \
  -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

`toolchain.cmake`：

```cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_SYSROOT /path/to/sysroot)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

## 7. 常见坑

| 坑 | 说明 |
|---|---|
| Tab/空格 | Makefile 命令行必须 Tab |
| 变量展开 | `=` vs `:=` |
| 头文件依赖缺失 | 改头文件不重编 |
| 交叉编译混库 | 主机库/目标库 |
| CMake 污染 | 源码内构建 |
| RPATH | 部署后找不到库 |
| 并行竞态 | 依赖没写全 |

## 8. 调试

```bash
make -n            # 只打印
make V=1           # 详细（若支持）
make --debug=v
cmake --build build --verbose
cmake -LAH         # 查看缓存变量
```

## 9. 工程建议

- 目标级属性优先于全局变量。
- 不在源码树内构建。
- 版本/工具链固定（容器）。
- 依赖显式声明，避免隐式链接。
- 构建产物/中间文件不入库。

## 10. 相关

- [构建系统总览](../../7.平台与集成/2.构建系统/00-总览.md)
- [Buildroot](../../7.平台与集成/2.构建系统/04-Buildroot.md)
- [Yocto](../../7.平台与集成/2.构建系统/03-Yocto/00-总览.md)
- [代码质量与测试](../../2.计算机科学/5.软件工程/01-代码质量与测试.md)
