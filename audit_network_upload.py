#!/usr/bin/python

# Usage:
# $ python3 audit_network_upload.py ~/data/mainnet/geth.ipc --score_contract <addr> --send
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

def _load_env_file(path: str):
    try:
        if not os.path.exists(path):
            return False
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                if k.startswith('export '):
                    k = k[len('export '):].strip()
                v = v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                if k and (k not in os.environ):
                    os.environ[k] = v
        return True
    except Exception:
        return False

def _load_dotenv():
    cwd_env = os.path.join(os.getcwd(), '.env')
    script_env = os.path.join(os.path.dirname(__file__), '.env')
    if not _load_env_file(cwd_env):
        _load_env_file(script_env)

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

def get_month_start():
    now = datetime.now()
    return int(datetime(now.year, now.month, 1).timestamp())

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
            {"internalType": "uint32[]", "name": "coreIds", "type": "uint32[]"},
            {"internalType": "uint32[]", "name": "dates", "type": "uint32[]"},
            {"internalType": "uint8[]", "name": "nodeTypes", "type": "uint8[]"},
            {"internalType": "bool[]", "name": "livenesses", "type": "bool[]"},
            {"internalType": "bool[]", "name": "checkins", "type": "bool[]"},
            {"internalType": "uint256[]", "name": "points", "type": "uint256[]"}
        ],
        "name": "recordBatch",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# 必须从 core_nodes.json 加载
core_nodes = []
json_path = os.path.join(os.path.dirname(__file__), 'core_nodes.json')
if os.path.exists(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            loaded_nodes = json.load(f)
            if isinstance(loaded_nodes, list) and len(loaded_nodes) > 0:
                core_nodes = loaded_nodes
                print(f"Loaded core_nodes from {json_path} ({len(core_nodes)} entries)")
            else:
                raise Exception("core_nodes.json is empty or invalid format")
    except Exception as e:
        raise Exception(f"Failed to load core_nodes.json: {e}")
else:
    raise Exception(f"core_nodes.json not found at {json_path}")

parser = argparse.ArgumentParser('audit_network_upload')
parser.add_argument('geth_ipc', help='path to geth.ipc file to be attached to')
parser.add_argument('--score_contract', help='AuditPoints contract address to record daily points', default=None)
parser.add_argument('--date', help='target biz date (UTC+8) in YYYYMMDD (default: yesterday in UTC+8)', default=None)
parser.add_argument('--today', help='use current biz date (UTC+8) at counting moment', action='store_true')
parser.add_argument('--send', help='actually send recordBatch tx (default: dry-run)', action='store_true')
args = parser.parse_args()

_load_dotenv()

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
last_block_t = datetime.fromtimestamp(last_block.timestamp)
current_t = datetime.now()
diff_t = current_t - last_block_t

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

print('Jouleverese Network Audit Report')
print('===============================================')
print('Report Time:', datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z"))
print('------------- blockchain status ---------------')

if diff_t < timedelta(seconds=60):
    print('Blockchain Status: 🟢')
else:
    print('Blockchain Status: 🔴')

print('Latest Block Height:', last_block_n)
print('Latest Block Time:', last_block_t.astimezone())
print('Business Time (UTC+8):', biz_dt.strftime('%Y-%m-%d %H:%M:%S +0800'))
print('Target Biz Date (UTC+8):', target_date_int)

# 连接与节点聚合
audit_node_id = w3.geth.admin.node_info().id
all_peers = w3.geth.admin.peers()
all_connected_ids = functools.reduce(lambda ids, n: ids+[n.id], all_peers, [])

all_nodes = {}
all_miners = {}
for node in core_nodes:
    # 必须包含 id, type, ip
    if 'id' not in node or 'type' not in node or 'ip' not in node:
        print(f"Skipping invalid node entry: {node}")
        continue

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
count = count_miner = count_witness = 0
for (id, node) in all_nodes.items():
    node_type = node['type']
    if node_type == 'miner':
        node['block_rate'] = all_miners.get(node.get('signer', '').lower(), {}).get('block_rate') or -1
        if node['block_rate'] > 0:
            count_miner += 1
            count += 1
    elif node_type in ['witness', 'witness(a)']:
        ww3 = Web3(Web3.HTTPProvider('http://' + node['ip'] + ':8501'))
        if ww3.is_connected():
            try:
                node['block_height'] = ww3.eth.get_block_number()
            except Exception:
                node['block_height'] = 0
        else:
            node['block_height'] = 0
        
        diff_blocks = abs(node['block_height'] - last_block_n)
        if diff_blocks < 10:
            count_witness += 1
            count += 1

## reporting node counts
print('Network Size: ', count, ' nodes (', count_miner, ' miners, ', count_witness, ' witnesses, miner*s excluded)')

## reporting node status
print('---------------- nodes status -----------------')
print('TYPE', 'SINCE', 'IP', 'CONNECTED', 'STATUS', 'ACTIVITY', 'LIVENESS', 'CORE-ID', 'OWNER', 'CHECK-IN')
print('-----------------------------------------------')

no_check_in_list = []
no_kyc_list = []

## helper: reporting func
def report(node):
    enode_connected = '🟢' if node['status'] == 'connected' else '🟡'
    if node['type'] == 'miner' and node['block_rate'] > 0:
        node_liveness = '🟩'
        node_activity = node['block_rate']
    elif node['type'] in ['witness', 'witness(a)'] and node['block_height'] > 0:
        node_liveness = '🟩'
        node_activity = node['block_height']
    else:
        node_liveness = '🟥'
        node_activity = -1

    # 获取节点的 check-in 状态
    core_id = node.get('coreId')  # 获取 coreId，可能为 None
    if core_id is not None:
        check_in_status = False 
        check_in_status_display = '❌' 
        try:
            token_info = jvcore_contract.functions.tokenURI(core_id).call()
            if token_info:
                token_info = formatTokenURI(token_info)
                if token_info:
                    month_start_timestamp = get_month_start() 
                    last_checkin_time = int(token_info.get('lastCheckInTime') or 0)
                    if last_checkin_time and last_checkin_time > month_start_timestamp:
                        check_in_status = True
                        check_in_status_display = '✅' 
        except Exception:
            pass
                
        if not check_in_status and node['owner'] not in no_check_in_list:
            no_check_in_list.append(node['owner'])
    else:
        core_id = '--'
        check_in_status_display = '❓'  # 缺失 coreId，显示为未知状态
        if node['owner'] not in no_kyc_list:
            no_kyc_list.append(node['owner'])

    core_id_display = f'J-{core_id}'
    owner_display = f'"{node["owner"]}"'
    print(node['type'], node.get('since', 'N/A'), node['ip'], enode_connected, node['status'], node_activity, node_liveness, core_id_display, owner_display, check_in_status_display)

## reporting miner status first
for (id, node) in all_nodes.items():
    if node['type'] == 'miner':
        report(node)

## reporting this audit node
if audit_node_id in all_nodes:
    report(all_nodes[audit_node_id])

## reporting miner*
for (id, node) in all_nodes.items():
    if node['type'] == 'miner*':
        report(node)

## reporting witness alive
for (id, node) in all_nodes.items():
    if node['type'] == 'witness' and node['block_height'] > 0:
        report(node)

## reporting witness suspicious to not alive anymore
for (id, node) in all_nodes.items():
    if node['type'] == 'witness' and node['block_height'] == 0:
        report(node)


if no_check_in_list or no_kyc_list:
    print('---------------- notice -----------------')

    if no_check_in_list:
        print("❌ NO CHECK-IN:", ','.join(no_check_in_list))

    if no_kyc_list:
        print("❓ NO KYC:", ','.join(no_kyc_list))


# 聚合到人（coreId）维度，判定 liveness 与 check-in
def role_bp(alive: bool, checkin: bool) -> int:
    if alive and checkin:
        return 100
    elif alive and not checkin:
        return 10
    else:
        return 0

# 节点类型枚举与常量（与合约一致：0=MINER, 1=WITNESS）
NODE_MINER = 0
NODE_WITNESS = 1

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

core_ids = []
dates = []
node_types = []
livenesses = []
checkins = []
points = []

for core_id, entry in per_person.items():
    try:
        cid = int(core_id)
    except Exception:
        continue
    if cid < 0 or cid > 0xFFFFFFFF:
        continue
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

    # MINER 记录
    core_ids.append(cid)
    dates.append(int(target_date_int))
    node_types.append(NODE_MINER)
    livenesses.append(bool(entry['minerAlive']))
    checkins.append(bool(is_checkin))
    points.append(int(miner_bp))

    # WITNESS 记录
    core_ids.append(cid)
    dates.append(int(target_date_int))
    node_types.append(NODE_WITNESS)
    livenesses.append(bool(entry['witnessAlive']))
    checkins.append(bool(is_checkin))
    points.append(int(witness_bp))

print('------------- points recording ---------------')
print('Payload size:', len(core_ids), 'entries on date', target_date_int)
print('Sample payload:', {
    'coreId': core_ids[:3],
    'date': dates[:3],
    'nodeType': node_types[:3],
    'liveness': livenesses[:3],
    'checkin': checkins[:3],
    'points': points[:3]
})

if not args.score_contract:
    print('No --score_contract provided. Dry-run only.')
else:
    try:
        audit_points_address = Web3.to_checksum_address(args.score_contract)
    except Exception:
        raise Exception('invalid --score_contract address')

    if len(core_ids) == 0:
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
            tx = ap_contract.functions.recordBatch(core_ids, dates, node_types, livenesses, checkins, points).build_transaction({
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
            try:
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                print('Tx status:', receipt.status, 'gasUsed:', receipt.gasUsed)
                if receipt.status != 1:
                    print('Tx failed (likely revert). Check operator/coreId constraints.')
            except Exception as e:
                print('Waiting for receipt failed:', str(e))
