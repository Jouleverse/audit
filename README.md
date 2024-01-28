# audit

Audit scripts and their usage for monitoring Jouleverse.

## audit_network.py

```Note: @deprecated 旧审计脚本audit_network.js已废弃。```

用途：用于每日审计Jouleverse网络节点运行情况。

节点类型：1) witness - 见证节点；2) miner\* - 预备中的记账节点（已PoS质押，未投票）；3) miner - 记账节点。

### 审计项目

1. 区块链总体运行区块是否良好🟢
2. 记账节点enode连接情况🟩 ，以及出块率（0 < block rate < 1）✅
3. 见证节点enode连接情况🟩 ，以及 8501 rpc连通性及当前区块高度✅

miner\* 由于是中间过渡状态，故暂不检查出块率（没有），也不检查8501 rpc（为安全起见记账节点配置关闭了rpc），也不会统计到网络节点数量中。

### 使用方法

1) 将本脚本放到见证节点上：

```
git clone git@github.com:Jouleverse/audit.git
```

2) 安装python依赖库

```
pip install web3
```

2) 跑一下下述命令，观察运行结果是否正确：

```
python3 audit_network.py ~/data/mainnet/geth.ipc
```

注意：检查 ~/data/mainnet/geth.ipc 是否有足够权限访问

3) 执行 crontab -e ，添加定时任务，内容参见 audit_network.crontab

注意：访问geth.ipc的权限问题。确保定时任务能够顺利执行。

### 日常维护

新节点入网流程：

进节点预备群 -> 搭建节点 -> 报告搭建情况，大家审查 -> OK后，记账节点质押，见证节点不需要 -> 填写节点信息登记表 -> 添加审计 -> 见证节点入网成功；记账节点安排节点投票，投票通过后，检查出块无误，入网成功

在上述流程中，审计添加是确认节点入网的重要一步。

审计节点需要做的事情是：

1. 审查节点报告到节点群中的信息，判断其节点运行状态良好，符合要求。确认无误后，提醒他填写节点信息登记表
2. 根据登记信息，将该节点添加到audit_network.py脚本中。试运行一下，观察审计结果，确认节点接入正常
3. crontab -e 编辑定时任务，把该节点登记的email地址添加到每日审计报告发送的email列表尾部
4. 节点群周知大家，新节点成功纳入审计报告（可将第2步试运行的审计报告截图发群中）
5. 把更新后的audit_network.py和audit_network.crontab 推送到github 并发 Pull Request 请求合并到主干

### TODO

- 记录每次检查结果，按月汇总可用率百分比，纳入报告，作为服务水平指标，供PoWh激励参考
  - witness 见证节点 
    - 每小时请求一次节点RPC，查询区块高度，正常返回区块高度 + 区块高度相差不小于 x (待定)，即为有效
    - 按月统计，可用率达到 99% 为合格节点 
    - 举例：2024年1月 有31天，24 * 31 = 744，744 * 99% = 736，有效记录大于 736 次，为合格节点


### Revision History

2023.10.18: 0.1 evan.j

2023.10.26: 0.1.1 evan.j + Angel witness

2023.10.28: 0.1.2 evan.j + Menger 比尔盖 miners, - Menger witness

...

2024.1.15: 0.2.1 evan.j
- auto detect if I am the audit node
- put it to github repo audit/, open for anyone to audit

0.2.2 evan.j
- add enode infos for all nodes, and automatically addPeer if not seeing it.

...

2024.1.16: handover audit responsibility to Jeff

2024.1.24: evan.j: python rewrite using web3

