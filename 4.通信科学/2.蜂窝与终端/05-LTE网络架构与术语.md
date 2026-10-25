---
id: "cell-05"
title: "LTE网络架构与术语"
cluster: cell
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["lte"]
aliases: ["LTE网络架构与术语"]
created: 2026-10-24
updated: 2026-10-24
---
# LTE网络架构与术语


## LTE 网络架构


![LTE 网络架构](assets/LTE%20%E7%BD%91%E7%BB%9C%E6%9E%B6%E6%9E%84.jpg)   

## 网络组成
LTE采用扁平化的网络结构，接入网仅包含Node B，不再有RNC。   
整个LTE/SAE 系统由核心网EPC、基站eNode B和用户设备UE 三部分组成。   
EPC负责核心网部分，其边界节点MME负责信令处理，另一边界节点SAE Gateway(S-GW)负责数据处理。eNode B负责接入网部分，也称E-UTRAN。UE指终端用户设备。   

eNode B与EPC通过S1接口连接，eNode B之间通过X2接口连接，eNode B通过Uu接口连接。   

## 功能
eNB：RRM功能、IP头压缩及用户数据流加密、UE附着时的MME选择、上行数据向S-GW的路由、寻呼消息的调度传输、广播消息的调度传输、为移动性和调度进行测量、调度和发送ETWS消息。   
MME：NAS信令及其安全、AS安全控制、3GPP系统间移动时的CN节点间的信令交互、空闲模式下的UE可及性管理、跟踪区列表管理、P-GW和S-GW的选择、跨MME切换时的MME选择、切换到GERAN或UMTS系统时的SGSN选择、漫游管理、用户认证、承载管理、ETWS支持。   
S-GW：跨eNB切换时的本地移动锚定、跨3GPP移动时的锚定、E-UTRAN空闲模式下行包缓冲及发起网络触发的业务请求、合法监听、分组路由和转发、上下行传输级包标记、为运营商间计费统计用户和QCI粒度，以及对每UE、PDU及QCI进行上下行计费。   
P-GW：基于每用户的包过滤、合法监听、UE IP地址分配、下行传输级包标记，上下行业务级计费、网关和速率限制，基于APN-AMBR的下行速率限制。   

一个国家内由一个运营商运营的网络叫做公众陆地移动通信网PLMN。漫游，即用户可以里拦截到除本身归属PLMN以外的其他PLMN。   

S-GW作为与其他3GPP技术间互操作的“移动性锚链”，P-GW作为另一“移动性锚链”允许与注入cdma2000或WiMAX等非3GPP网络间的无缝切换。   

RRC再接入层协议栈中被称为“层3”，其在接入层中起主要控制作用，负责建立无线承载和配置eNode B和UE间由RRC信令控制的所有底层。   

## 接入网和核心网的功能划分
![接入网和核心网功能划分](assets/%E6%8E%A5%E5%85%A5%E7%BD%91%E5%92%8C%E6%A0%B8%E5%BF%83%E7%BD%91%E5%8A%9F%E8%83%BD%E5%88%92%E5%88%86.jpg)   

E-UTRAN 提供空中接口功能(物理层、MAC、RLC、PDCP、RRC)，另外还提供对无线资源的动态资源分配、对eNB的测量的配置、对空口接入的接纳控制、连接的移动性控制、RB控制和小区间的RRM功能。   
EPC 通过控制平面和用户平面节点完成移动性锚点功能、UE的IP地址分配、分组过滤、NAS信令处理和安全性、空闲状态的移动性管理以及EPS承载控制功能。   

### 核心网
主要逻辑点：PDN网关、业务网关、移动性管理实体MME、用户归属服务器HSS、策略控制和计费规则功能(PCRF)。   

#### PCRF
负责策略控制的决策，也负责位于P-GW中策略控制加强功能(PCEF)中基于流量收费的功能。   

#### 归属位置寄存器 HLR
HLR包含用户的SAE开户信息。   

#### P-GW
负责用户IP地址分配和QoS保证，并根据PCRF规则进行基于流量的计费。   

#### S-GW
用户IP数据包通过S-GW发送。   

#### MME
处理UE和核心网络间信令交互的控制节点。UE和核心网络间所执行的协议栈称为非接入层协议(NAS)   

### 接入网
LTE的接入网仅由eNode B网络组成。   
eNode B与UE间的协议为接入层协议(AS)。   

## S1 接口
S1 接口把eNode B 连接到EPC。S1又分为两个接口，一个用于控制平面，另一个用于用户平面。   

### S1 协议结构
S1 协议结构时基于全IP协议传输栈。   

#### 控制平面
![S1控制平面](assets/S1%E6%8E%A7%E5%88%B6%E5%B9%B3%E9%9D%A2.jpg)   

#### 用户平面
![S1用户平面](assets/S1%E7%94%A8%E6%88%B7%E5%B9%B3%E9%9D%A2.jpg)   

### S1 接口初始化
S1-MME 控制平面接口初始化首先始于鉴别与eNode B必须连接的MME，接着是传输网络层TNL的建立。   
在LTE中S1-flex(灵活连接)功能支持下，eNode B 必须向它所属的池区中的每一个MME节点初始化一个S1接口。池区中MME节点列表和初始的相应远程IP地址可在部署时由eNode B直接配置。该eNode B随后用这个IP地址启动TNL建立。在一个eNode B 和一个MME之间只建立一个SCTP组合。   
一旦TNL进阿里，一些用于系统操作的基本应用程序级配置数据在eNode B和MME间通过eNode B发起的“S1建立”流程自动交换。   
一旦S1建立流程完成，S1接口即可以使用。   

### S1 接口的上下文管理
![S1 上下文](assets/S1%20%E4%B8%8A%E4%B8%8B%E6%96%87.jpg)   
在每一池区内，UE驻留在该池区期间的通信都与一个特定的MME相关联。这就需要在这个MME中为用户终端创建一个上下文。这一特定的MME是由UE进入该池区的第一个eNode B节点中的“NAS节点选择功能”(NNSF)来选定的。   

### S1 接口的承载管理
LTE使用独立的专用流程来分别进行承载的建立、更改和释放。   
对于每个请求建立的承载，传输层地址和隧道端点在“承载设置请求”消息中提供给eNode B以指示S-GW中承载的终点，即上行用户平面数据必须发送到的地方。eNode B在“承载建立响应”消息指示eNode B的承载终点，即下行用户平面数据必须发送到的地方。   

### 通过S1 接口的寻呼

### S1接口上的移动性
![S1接口移动性](assets/S1%20%E6%8E%A5%E5%8F%A3%E7%A7%BB%E5%8A%A8%E6%80%A7.jpg)    

### S1 接口上的负荷管理
S1接口又三类负荷管理流程：分发业务时通常的“负荷均衡”过程。克服加载中突发峰值的“过载”流程。部分/完全卸载MME的“负荷再均衡”过程。   

MME负载均衡流程的目的在于根据池区中MME的各自的能力公平地向MME分发业务。   

## X2
X2接口用于eNode B连接。   

### X2协议结构
X2 接口的协议结构与S1接口相同。   
![X2协议结构](assets/X2%E5%8D%8F%E8%AE%AE%E7%BB%93%E6%9E%84.jpg)   

### X2接口初始化
X2 接口可在一个eNode B 与其相邻的若干eNode B间建立，在需要时交换信令信息。   

X2 接口初始化首先要确定一个合适邻居，然后建立TNL。一旦TNL建立完毕，初始eNode B必须触发X2建立流程(与S1接口流程建立相似)。   

### X2 接口移动性
![X2 接口移动性](assets/X2%20%E6%8E%A5%E5%8F%A3%E7%A7%BB%E5%8A%A8%E6%80%A7.jpg)   

### X2 接口上的负载和干扰管理

### X2 接口上的UE历史信息
UE历史信息包括诸如UE最近访问过的小区和在每个小区的访问时间。

## 术语


GSM Global System for Mobile Communications 全球移动通讯系统
TDMA Time division multiple access 时分多址   
CDMA Code Division Multiple Access 码分多址   
FDMA Frequency Division Multiple Access 频分多址   
GPRS General Packet Radio Service 通用封包无线服务   
UTRA Universal Terrestrial Radio Access 通用地面无线电接入   
UTRAN UMTS Terrestrial Radio Access Network UMTS的陆地无线接入网   
GERAN GSM EDGE Radio Access Network GSM/EDGE 无线通讯网络
E-UTRAN Evolved UMTS Terrestrial Radio Access Network 演进的UMTS陆地无线接入网
UMTS Universal Mobile Telecommunications System 通用移动通讯系统   
WCDMA Wideband Code Division Multiple Access宽带码分多址 -->UMTS-FDD、UTRA-FDD   
TD-SCDMA Time Division - Synchronous Code Division Multiple Access 时分-同步码分多址   
EDGE Enhanced Data rates for GSM Evolution GSM增强数据率演进   
HSPA High Speed Packet Access 高速分组接入   
HSDPA High Speed Downlink Packet Access 高速下行分组接入   
HSUPA High Speed Uplink Packet Access 高速上行分组接入   
LTE Long Term Evolution 长期演进技术   
ITU The International Telecommunication Union 国际电信联盟   
FDD Frequency Division Duplexing 频分双工   
TDD Time Division Duplexing 时分双工   
MIMO Multi-input Multi-output 多输入多输出系统(多天线技术)   
HOM 高阶调制   
CPC 持续包连接   
RAN Radio Access Network 无线电接入   
CN Core Network 核心网   
RF Radio frequency 射频   
MBMS Multimedia Broadcast Multicast Service 多媒体广播多播业务   
IMS IP Multimedia Subsystem IP多媒体子系统   
EPC Evolved Packet Core network 分组交换核心网   
eNode B 基站   
UE 用户设备   
RB 无线承载   
RRM Radio Resource Management 无线资源管理   
HARQ Hybrid Automatic Repeat Request 混合自动重传请求   
ARQ Automatic Repeat-reQuest 自动重传请求   
NAS Non-access stratum 非接入层   
RNC Radio Network Controller 无线网络控制器   
OFDM Orthogonal Frequency Division Multiplexing 正交频分复用技术   
OFDMA Orthogonal Frequency Division Multiple Access 正交频分多址   
SC-FDMA Single-carrier Frequency-Division Multiple Access 单载波频分多址   
CA Carrier Aggregation 载波聚合   
TTI Transmission Time Interval 传输时间间隔   
PRB Physical Resource Block 物理资源块   
VBS Virtual Resource Block 虚拟资源块   
QPSK Quadrature Phase Shift Keying 正交相移键控   
QAM Quadrature Amplitude Modulation 正交幅度调制   
SFBC Space Frequency Block Code 空间频率分组码   
FSTD Frequency Switch Transmit Diversity 频率切换发送分集   
PSS Primary Synchronization Signal 主同步信号   
SSS Secondary Synchronization Signal 辅同步信号   
MME Mobility Management Entity 网络节点   
ETWS Earthquake and Tsunami Warning System 地震和海啸预警系统   
EPS Evolved Packet System 演进分组系统   
SCTP Stream Control Transmission Protocol 流控制传输协议   
CS Circuit Switch 电路交换   
PS PacketSwitch 分组交换   
PLMN Public Land Mobile Network 公共陆地移动网   
RSSI Received Signal Strength Indication 接收的信号强度指示   

## MIMO
广义来说，MIMO泛指在发射端和接收端同时采用多天线。   
设计思想：利用无线传输环境的某些特性，通过并行地发射多个数据流来获得较高的数据速率。   

## LTE 简述
LTE 支持1.4MHz 3MHz 5MHz 10MHz 15MHz 20MHz几种带宽分配方式。   
2004年正式提出LTE概念并开始相关研究工作。   
长期演进的目标：降低时延，提高用户数据速率，改善系统容量以及覆盖，降低运营商的成本。   
整个EPS系统由核心网、基站和用户设备三个部分组成。其中，EPC负责核心网部分，EPC信令处理部分称为MME，数据处理部分称为SAE Gateway(S-GW)，eNode B负责接入网部分，也称作E-UTRAN。   
eNB功能：RRM功能，IP头压缩及用户数据流加密，UE附着时的MME选择，寻呼信息的调度传输，广播信息的调度传输以及设置和提供eND的测量。   
MME功能：寻呼消息发送，安全控制，Idle态的移动性管理，SAE承载管理以及NAS信令的加密及完整性保护。   
S-GW功能：数据的路由和传输，用户面数据的加密。   

### 空中接口协议
LTE无线接口协议包括物理层(PHY)，媒体接入控制层(MAC)，无线链路控制层(RLC)，分组数据汇聚协议层(PDCP)，无线资源控制层(RRC)   
PHY:物理层向高层提供数据传输服务   
MAC:媒体接入控制层主要实现与调度和HARQ相关的功能   
RLC:无线链路控制层实现与ARQ相关的功能   
PDCP:分组数据汇聚协议层   
RRC:无线资源控制层   


#### 控制面
![控制面](assets/%E6%8E%A7%E5%88%B6%E9%9D%A2.jpg)   
![控制平面协议栈](assets/%E6%8E%A7%E5%88%B6%E5%B9%B3%E9%9D%A2%E5%8D%8F%E8%AE%AE%E6%A0%88.jpg)   

#### 用户面
![用户面](assets/%E7%94%A8%E6%88%B7%E9%9D%A2.jpg)   
![用户平面协议栈](assets/%E7%94%A8%E6%88%B7%E5%B9%B3%E9%9D%A2%E5%8D%8F%E8%AE%AE%E6%A0%88.jpg)   

### LTE射频
射频信号处理是无线通信系统中的重要组成部分，它是连接射频信号传输媒介和基带信号处理部分的重要接口。   

## 其他无线通信系统
### cdma2000
cdma2000是IS-95基础上发展的蜂窝移动通信标准，后来又成为IMT-2000技术家族的一部分。   

### WiMAX
WiMAX是基于IEEE 802.16 标准家族的宽带无线接入的惯称。   
IEEE 802.16是一个无线城域网(MAN)标准。   

## IMT-Advanced
IMT-Advanced系统为具有超过IMT-2000能力的新的移动系统。   

## LTE-A
LTE-A是LTE-Advanced的简称，是LTE技术的后续演进。
