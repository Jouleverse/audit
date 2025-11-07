#!/usr/bin/python

# Usage:
# $ python3 audit_network_utc8_test.py ~/data/mainnet/geth.ipc --score_contract <addr> --send
#
# - 默认干跑（dry-run），仅打印上链载荷；加上 --send 才会真正发送交易。
# - 调度建议：UTC+8 每日 00:05–00:30（推荐 00:10）执行，写入“昨日(UTC+8)”的业务日期。

import argparse
import os
import json
import functools
import base64
from datetime import datetime, timedelta
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

# 业务时区：UTC+8 的日期口径与月度边界
UTC8_OFFSET_SECS = 8 * 3600

def _fmt_date_yyyymmdd(dt: datetime) -> int:
    return int(dt.strftime('%Y%m%d'))

def _month_key_from_date(date_yyyymmdd: int) -> int:
    yyyy = date_yyyymmdd // 10000
    mm = (date_yyyymmdd // 100) % 100
    return int(yyyy * 100 + mm)

def _biz_dt_from_chain_ts(chain_ts: int) -> datetime:
    # 以链上 UTC 时间为基准，加 8 小时得到业务日的本地时间（UTC+8）
    return datetime.utcfromtimestamp(chain_ts) + timedelta(seconds=UTC8_OFFSET_SECS)

def _biz_date_from_chain_ts(chain_ts: int) -> int:
    return _fmt_date_yyyymmdd(_biz_dt_from_chain_ts(chain_ts))

def _max_date_from_chain_ts(chain_ts: int) -> int:
    # 允许“未来 24 小时窗口”：max_date = (biz_ts + 86400) 的 UTC+8 业务日期
    biz_dt = _biz_dt_from_chain_ts(chain_ts) + timedelta(days=1)
    return _fmt_date_yyyymmdd(biz_dt)

def _month_start_ts_utc8_from_chain_ts(chain_ts: int) -> int:
    # 月度边界按 UTC+8 的 1号 00:00:00，返回 UTC 时间戳用于与 lastCheckInTime(UTC) 比较
    biz_dt = _biz_dt_from_chain_ts(chain_ts)
    month_start_biz_dt = datetime(biz_dt.year, biz_dt.month, 1)
    month_start_utc_dt = month_start_biz_dt - timedelta(seconds=UTC8_OFFSET_SECS)
    return int(month_start_utc_dt.timestamp())

def _validate_yyyymmdd(date_int: int) -> bool:
    # 简单有效性校验（YYYYMMDD，月/日范围）
    try:
        yyyy = date_int // 10000
        mm = (date_int // 100) % 100
        dd = date_int % 100
        if yyyy < 2000 or yyyy > 9999:
            return False
        if mm < 1 or mm > 12:
            return False
        if dd < 1 or dd > 31:
            return False
        # 不做闰月/大小月复杂校验，避免过度复杂；若需要可后续增强
        return True
    except Exception:
        return False

def formatTokenURI(data_str: str):
    import json
    if 'application/json;base64' in data_str and ',' in data_str:
        data_str = data_str.split(',')[1]
        json_str = base64.b64decode(data_str).decode('utf-8')
        data_obj = json.loads(json_str)
        return data_obj
    return None

# JVCore 合约 ABI/地址与 AuditPoints ABI（与现有 audit_network.py 保持一致）
jvcore_abi = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "isLiveness",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "tokenURI",
        "outputs": [
            {"internalType": "string", "name": "", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

jvcore_address = "0x8d214415b9c5F5E4Cf4CbCfb4a5DEd47fb516392"

audit_points_abi = [
    {
        "inputs": [
            {"internalType": "uint256[]", "name": "tokenIds", "type": "uint256[]"},
            {"internalType": "uint32[]", "name": "dates", "type": "uint32[]"},
            {"internalType": "bool[]", "name": "livenesses", "type": "bool[]"},
            {"internalType": "bool[]", "name": "checkins", "type": "bool[]"},
            {"internalType": "uint16[]", "name": "minerBPs", "type": "uint16[]"},
            {"internalType": "uint16[]", "name": "witnessBPs", "type": "uint16[]"}
        ],
        "name": "recordBatch",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "uint32", "name": "monthKey", "type": "uint32"}
        ],
        "name": "getMonthlyPoints",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# 从现有脚本复制的 core_nodes 列表，确保测试载荷与生产一致
core_nodes = [
        {
            'owner': 'JNSDAO',
            'type': 'witness',
            'ip': '101.32.253.192',
            'id': '2379e2c19b8a0e4a76d011b07e41493902c1f274abc5adce3e20fe60f0cabac6',
            'enode': 'enode://19dc6b15744e8ad73f860d6ca7bf7b1acf37497ef8a720a88d64449ec837af460535fcf01662907aaece6bde0c2ff539a9d79e353d043769134666a1586fa4e0@43.134.121.187:30311',
            'since': '20230529',
            'coreId': 25,
            },
        {
            'owner': 'Jeff',
            'type': 'witness',
            'ip': '43.136.53.164',
            'id': '36d1c18a197fea99e9b55b111b03ab03866367838b3017ae91984e0648e3f677',
            'enode': 'enode://f3e4e524d89b4cdb9ee390d9485cee4d6a5e9a260f5673cab118505cc3e69fe8365bc00434222d27fe4082ca798b13ad8e7e139d1315f635fd0e46dbe96fa809@43.136.53.164:30311',
            'since': '20240115',
            'coreId': 29,
            },
        {
            'owner': 'Koant',
            'type': 'miner',
            'ip': '119.29.202.168',
            'id': '93886caf6ba2a9b4cf31527385b53f7750dd8d6a3fcfaa41cb6c59a77c049ec6',
            'signer': '0x8d6a6f3d18f0d378ecb75796c4ebc8f54fba7700',
            'enode': 'enode://a475b2061e5b46e7a962541da252654d8629254c38ed4fb3410fe9a6240e40f3502c91f99ab5e82956bb91f028e76b4adf07659139736a4f19d8e19da824eba9@119.29.202.168:30311',
            'since': '20231015',
            'coreId': 0,
            },
        {
            'owner': '谢勇',
            'type': 'miner',
            'ip': '82.157.251.101',
            'id': '6f0ef352cc2536d91f0a55efbec480c8e2b76a11fc5c30830167e026327f0a18',
            'signer': '0x93196aeEb56fe0F5672d84b8F50C123b5dA50329',
            'enode': 'enode://c43fa0ea62dfc0e09906f67a8b730918cbe567a3f53322470780ecdc569efda1a2dd9e4707ac65e3b558e9bf8a025a22da33b1ad08211290211b8c5ed0ed1671@82.157.251.101:30311',
            'since': '20240119',
            'coreId': 18,
            },
        {
            'owner': 'Jacky',
            'type': 'miner',
            'ip': '47.94.93.119',
            'id': 'e88e333abc2dce665fd9c35bef4a0383249b1670955cefac4c582092fa34fbcb',
            'signer': '0x28D314d2B00EED89041843d4Cd7b9de91170f37a',
            'enode': 'enode://be96ad65107a3d520943f761d00a79a6e08bd4acc5b008b58ff8406761e5ca7e923bcb310654089b1ab364579f70ebe042f2baf9c9adbfa8482052f31c6766f1@47.94.93.119:30311',
            'since': '20230529',
            'coreId': 9,
            },
        {
            'owner': '教链',
            'type': 'miner',
            'ip': '82.157.210.13',
            'id': '61cb546c70e6a470e8ee64c4ff5fbef138d9afe116fb24147636802d6ffac30b',
            'signer': '0x85db5D64BD1a2652A75C4A7e12Eeba2f43c57bC4',
            'enode': 'enode://d667d09c38706d40fa1c15cde8dc28c117087cdf55d41d402d70b0817636c6f65e6a6463e81ab178ad9a896ea93c37b479a01ff19dfe13cd4276ea2c64575c76@81.68.150.141:30311',
            'since': '20230524',
            'coreId': 25,
            },
        {
            'owner': 'Menger',
            'type': 'miner',
            'ip': '62.234.21.37',
            'id': '16376be08813c07d06cdf5e073916f97846c67ec08f1f9c3be4ac5d894ab4670',
            'signer': '0x3fc084c968e77f264803ef5af09e6d6f05228bea',
            'enode': 'enode://72ced57bb2a447947d7bf6378ee927fb04954eba69063571bec3cd3e3cf8d5e660ffb3e62a2cf073045f949a592b2a2c66a1d5bf700a00f069531239749a8382@62.234.21.37:30311',
            'since': '20231027',
            'coreId': 5,
            },
        {
            'owner': '严光红',
            'type': 'miner',
            'ip': '106.53.60.230',
            'id': 'f92367cc2a9b02c68d6f024b7630bdfa6060d0ce70fc676696633a59eef3ae39',
            'signer': '0xcce6cc1ba66c6b9af2c7b20d78155c74ed9aad6f',
            'enode': 'enode://94b45bc3705c8abebeda0ee9b31a76188b59c0c69397362e96accd39b15a56668775204d4f2e3e7ddb2b14df0b640b5bb9cd4dcb60c252ef80268f1af815f623@106.53.60.230:30311',
            'since': '20240109',
            'coreId': 26,
            },
        {
            'owner': 'li17',
            'type': 'miner',
            'ip': '47.100.5.124',
            'id': 'ffd502a7cebcaad58aff75d9dfde768067d3e78baf31870a7f4debf353107581',
            'signer': '0x002ed4ea787fd611f44a8277b5e204aad5c81717',
            'enode': 'enode://b7055440d2792887e10ca12192d5d30200a4d9352d9de560732589014e26e5b6c587c5ae201441597795f33b2af6afecadb31193bf6f467024e3144ba40f6d2b@47.100.5.124',
            'since': '20240107',
            'coreId': 6,
            },
        # 其余 witness/miner 列表同现有脚本，已简化；如需完全一致，可继续扩充
]

# 优先从共享 JSON 加载 core_nodes，保证与生产脚本一致；不存在则使用上面的内置列表作为回退
try:
    json_path = os.path.join(os.path.dirname(__file__), 'core_nodes.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            loaded_nodes = json.load(f)
            if isinstance(loaded_nodes, list) and (len(loaded_nodes) == 0 or isinstance(loaded_nodes[0], dict)):
                core_nodes = loaded_nodes
                print(f"Loaded core_nodes from {json_path} ({len(core_nodes)} entries)")
except Exception as e:
    print('Warning: failed to load core_nodes.json:', e)

parser = argparse.ArgumentParser('audit_network_utc8_test')
parser.add_argument('geth_ipc', help='path to geth.ipc file to be attached to')
parser.add_argument('--score_contract', help='AuditPoints contract address to record daily points', default=None)
parser.add_argument('--date', help='target biz date (UTC+8) in YYYYMMDD (default: yesterday in UTC+8)', default=None)
parser.add_argument('--today', help='use current biz date (UTC+8) at counting moment', action='store_true')
parser.add_argument('--send', help='actually send recordBatch tx (default: dry-run)', action='store_true')
args = parser.parse_args()

geth_ipc = args.geth_ipc
w3 = Web3(Web3.IPCProvider(geth_ipc))
if not w3.is_connected():
    raise Exception('cannot attach to geth ipc: ' + str(geth_ipc))

w3.middleware_onion.inject(geth_poa_middleware, layer=0)

jvcore_contract = w3.eth.contract(address=jvcore_address, abi=jvcore_abi)

# 获取链时间与区块
last_block_n = w3.eth.get_block_number()
last_block = w3.eth.get_block(last_block_n)
chain_ts = int(last_block.timestamp)
chain_dt_utc = datetime.utcfromtimestamp(chain_ts)
biz_dt = _biz_dt_from_chain_ts(chain_ts)

# 目标日期：默认写入“昨日(UTC+8)”
if args.date:
    try:
        target_date_int = int(args.date)
    except Exception:
        raise Exception('invalid --date, expecting YYYYMMDD')
else:
    if args.today:
        target_date_int = _fmt_date_yyyymmdd(biz_dt)
    else:
        target_date_int = _fmt_date_yyyymmdd(biz_dt - timedelta(days=1))

if not _validate_yyyymmdd(target_date_int):
    raise Exception('invalid target date: ' + str(target_date_int))

max_date_int = _max_date_from_chain_ts(chain_ts)
month_start_ts = _month_start_ts_utc8_from_chain_ts(chain_ts)

print('Jouleverese UTC+8 Test Writer')
print('===============================================')
print('Latest Block Height:', last_block_n)
print('Latest Block Time (UTC):', chain_dt_utc.isoformat())
print('Business Time (UTC+8):', biz_dt.strftime('%Y-%m-%d %H:%M:%S +0800'))
print('Target Biz Date (UTC+8):', target_date_int)
print('Max Allowed Date (UTC+8, +24h):', max_date_int)
if target_date_int > max_date_int:
    raise Exception('target_date exceeds max_date window; abort: ' + str(target_date_int) + ' > ' + str(max_date_int))

# 连接与节点聚合（与现有脚本一致的基本逻辑）
audit_node_id = w3.geth.admin.node_info().id
all_peers = w3.geth.admin.peers()
all_connected_ids = functools.reduce(lambda ids, n: ids+[n.id], all_peers, [])

all_nodes = {}
all_miners = {}
for node in core_nodes:
    all_nodes[node['id']] = node
    if node['type'] == 'miner':
        signer = node.get('signer')
        if signer:
            all_miners[signer.lower()] = node
    if node['id'] == audit_node_id:
        all_nodes[node['id']]['status'] = 'connected'
        all_nodes[node['id']]['type'] = 'witness(a)'
    elif node['id'] in all_connected_ids:
        all_nodes[node['id']]['status'] = 'connected'
    else:
        all_nodes[node['id']]['status'] = 'disconnected'
        try:
            w3.geth.admin.add_peer(node['enode'])
        except Exception:
            pass

# 获取 sealer 活跃度用于 miner 存活判断
try:
    clique_status = w3.provider.make_request('clique_status', [])['result']
    for (addr, n) in clique_status.get('sealerActivity', {}).items():
        if addr.lower() in all_miners:
            all_miners[addr.lower()]['block_rate'] = n / max(1, clique_status.get('numBlocks', 1))
except Exception:
    pass

# witness 高度与存活判断
for (id, node) in all_nodes.items():
    node_type = node['type']
    if node_type == 'miner':
        node['block_rate'] = all_miners.get(node.get('signer', '').lower(), {}).get('block_rate') or -1
    elif node_type in ['witness', 'witness(a)']:
        ww3 = Web3(Web3.HTTPProvider('http://' + node['ip'] + ':8501'))
        if ww3.is_connected():
            try:
                node['block_height'] = ww3.eth.get_block_number()
            except Exception:
                node['block_height'] = 0
        else:
            node['block_height'] = 0

# 聚合到人（coreId）维度，判定 liveness 与 check-in
def role_bp(alive: bool, checkin: bool) -> int:
    if alive and checkin:
        return 100
    elif alive and not checkin:
        return 10
    else:
        return 0

per_person = {}
for (_, node) in all_nodes.items():
    core_id = node.get('coreId')
    if not core_id:
        continue
    entry = per_person.get(core_id)
    if not entry:
        entry = {'minerAlive': False, 'witnessAlive': False}
        per_person[core_id] = entry
    node_type = node['type']
    if node_type == 'miner':
        alive = (node.get('block_rate', -1) or -1) > 0
        entry['minerAlive'] = entry['minerAlive'] or alive
    elif node_type in ['witness', 'witness(a)']:
        bh = node.get('block_height', 0) or 0
        alive = bh > 0 and abs(bh - last_block_n) < 10
        entry['witnessAlive'] = entry['witnessAlive'] or alive

token_ids = []
dates = []
livenesses = []
checkins = []
points_bps = []
miner_bps = []
witness_bps = []

for core_id, entry in per_person.items():
    is_checkin = False
    try:
        token_info = jvcore_contract.functions.tokenURI(core_id).call()
        if token_info:
            token_obj = formatTokenURI(token_info)
            if token_obj:
                last_checkin_time = int(token_obj.get('lastCheckInTime') or 0)
                is_checkin = last_checkin_time and last_checkin_time > month_start_ts
    except Exception:
        is_checkin = False

    miner_bp = role_bp(entry['minerAlive'], is_checkin)
    witness_bp = role_bp(entry['witnessAlive'], is_checkin)
    bp_sum = int(miner_bp + witness_bp)

    token_ids.append(int(core_id))
    dates.append(int(target_date_int))
    livenesses.append(bool(entry['minerAlive'] or entry['witnessAlive']))
    checkins.append(bool(is_checkin))
    points_bps.append(bp_sum)
    miner_bps.append(int(miner_bp))
    witness_bps.append(int(witness_bp))

print('------------- points recording (TEST) ---------------')
print('Payload size:', len(token_ids), 'entries on date', target_date_int)
print('Sample payload:', {
    'tokenId': token_ids[:3],
    'date': dates[:3],
    'liveness': livenesses[:3],
    'checkin': checkins[:3],
    'pointsBP': points_bps[:3],
    'minerBP': miner_bps[:3],
    'witnessBP': witness_bps[:3]
})

if not args.score_contract:
    print('No --score_contract provided. Dry-run only.')
else:
    try:
        audit_points_address = Web3.to_checksum_address(args.score_contract)
    except Exception:
        raise Exception('invalid --score_contract address')

    if len(token_ids) == 0:
        print('No eligible entries to record (missing coreId). Skip sending.')
    else:
        if not args.send:
            print('DRY-RUN: --send not specified. No transaction will be sent.')
        else:
            priv = os.environ.get('AUDITOR_PRIVATE_KEY')
            if not priv:
                raise Exception('missing AUDITOR_PRIVATE_KEY environment variable')
            acct = Account.from_key(priv)
            operator_addr = acct.address
            ap_contract = w3.eth.contract(address=audit_points_address, abi=audit_points_abi)
            tx = ap_contract.functions.recordBatch(token_ids, dates, livenesses, checkins, miner_bps, witness_bps).build_transaction({
                'from': operator_addr,
                'nonce': w3.eth.get_transaction_count(operator_addr),
                'gasPrice': w3.eth.gas_price,
            })
            try:
                tx['gas'] = w3.eth.estimate_gas(tx)
            except Exception:
                pass
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            print('Submitted recordBatch tx:', tx_hash.hex())