---
id: "sec-01"
title: "PKI 与设备证书"
cluster: sec
layer: L2
status: draft
confidence: medium
platform: []
source:
  - type: rfc
    ref: "RFC 5280 (X.509), RFC 8446 (TLS 1.3)"
verified_on: null
tags: ["pki", "certificate", "tls", "mtls"]
aliases: ["PKI", "证书"]
created: 2026-10-24
updated: 2026-10-24
---

# PKI 与设备证书

> 解决什么问题：设备如何证明"我是谁"，以及 HTTPS/TR-069/mTLS 的证书怎么发、怎么换、怎么排错。
> 不解决：具体 CA 平台操作。

## 1. 信任链

```text
Root CA（离线，长期）
  └── Intermediate CA（在线签发）
        └── Device Certificate（设备身份）
```

| 文件 | 内容 | 部署位置 |
|---|---|---|
| Root CA | 自签名证书 | 设备信任库 |
| Intermediate CA | 由 Root 签发 | 设备信任库/链 |
| Device cert | 设备公钥 + 身份 | 设备 |
| Device key | 私钥 | 设备安全存储（TPM/SE/加密分区） |

## 2. 证书关键字段

| 字段 | 说明 |
|---|---|
| Subject | `CN`/`O`/`OU`，设备常用序列号或 MAC |
| SAN | 现代 TLS 必须；IP/DNS |
| Key Usage | 数字签名/密钥加密 |
| Extended Key Usage | serverAuth/clientAuth |
| Validity | 有效期；设备时间必须正确 |
| Basic Constraints | CA/非 CA |
| CRL/OCSP | 吊销检查 |

## 3. 签发流程（设备侧）

```bash
# 1. 生成私钥与 CSR
openssl req -new -newkey rsa:2048 -nodes \
  -keyout device.key -out device.csr \
  -subj "/CN=SN123456/O=Vendor"

# 2. CA 签发
openssl x509 -req -in device.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out device.crt -days 365 -sha256

# 3. 校验
openssl verify -CAfile ca.crt device.crt
openssl x509 -in device.crt -noout -text
```

> 私钥必须在设备内生成，不应出厂统一烧录同一私钥。

## 4. TLS / mTLS

```bash
# 服务端校验客户端
openssl s_server -accept 443 -cert server.crt -key server.key -CAfile ca.crt -Verify 1

# 客户端校验服务端
openssl s_client -connect host:443 -CAfile ca.crt -servername host
```

要点：
- 关闭 `verify=False`；校验证书链与主机名。
- TLS 1.2+，禁用弱套件。
- 会话复用与 OCSP stapling 按性能需要开启。

## 5. 证书生命周期

| 阶段 | 要点 |
|---|---|
| 首次注入 | 产线安全注入；记录序列号与证书指纹 |
| 轮换 | 到期前自动续期；双证书过渡 |
| 吊销 | CRL/OCSP；失窃设备 |
| 备份 | 私钥不导出；CA 离线备份 |
| 审计 | 签发/吊销日志 |

## 6. 常见问题

| 现象 | 原因 |
|---|---|
| TLS 握手失败 | 时间不对、链不全、主机名不匹配 |
| `certificate verify failed` | 缺 Intermediate、根不在信任库 |
| 设备证书被拒 | EKU 不含 clientAuth、SAN 缺失 |
| 到期后集体离线 | 未做续期/告警 |
| 私钥泄露 | 统一烧录、日志打印、调试口可读 |

## 7. 待实测/待项目参数
- [ ] 目标产品的证书注入/轮换流程。
- [ ] CA 与设备信任库的清单。
- [ ] 一次证书过期导致 ACS 断连的案例。

## 8. 相关

- [TR-069](../1.%E7%BB%88%E7%AB%AF%E7%AE%A1%E7%90%86/01-TR-069.md)
- [TR-369](../1.%E7%BB%88%E7%AB%AF%E7%AE%A1%E7%90%86/02-TR-369.md)
- [IPsec](../2.%E9%9A%A7%E9%81%93%E4%B8%8EVPN/05-IPsec.md)
- [安全启动](../../11.%E5%BA%94%E7%94%A8%E4%B8%8E%E6%A1%88%E4%BE%8B/6.%E5%AE%89%E5%85%A8%E4%B8%8E%E5%90%88%E8%A7%84/01-%E5%AE%89%E5%85%A8%E5%90%AF%E5%8A%A8.md)
