#!/usr/bin/python

# Usage:
# $ python3 audit_network.py ~/data/mainnet/geth.ipc
# You may need to grant the access for ~/data/mainnet/geth.ipc to current user.

# Revision History:
# 2024.1.24 evan.j initial rewrite from the js version. add checks for rpc 8501 and block height of witness nodes.

import argparse
import os
import functools
import base64
from datetime import datetime, timedelta
from web3 import Web3
from web3.middleware import geth_poa_middleware
from core_nodes_config import core_nodes
from eth_account import Account
from audit_common import role_bp, month_start_ts_utc8_from_chain_ts, fmt_date_yyyymmdd, dedup_already_recorded, NODE_MINER, NODE_WITNESS, load_dotenv

# JVCore 合约 ABI
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
			{
				"internalType": "uint256",
				"name": "tokenId",
				"type": "uint256"
			}
		],
		"name": "tokenURI",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

# JVCore 合约地址
jvcore_address = "0x8d214415b9c5F5E4Cf4CbCfb4a5DEd47fb516392"
score_contract_default = "0xa1759e40313F07696Bc0F7974EE7454E7C58cc95"

## parse command line argument /path/to/geth.ipc
parser = argparse.ArgumentParser('audit_network')
parser.add_argument('geth_ipc', help='path to geth.ipc file to be attached to')
args = parser.parse_args()
geth_ipc = args.geth_ipc
load_dotenv()

## try to attach
w3 = Web3(Web3.IPCProvider(geth_ipc))
if not w3.is_connected():
    raise Exception('cannot attach to geth ipc: ', geth_ipc)

w3.middleware_onion.inject(geth_poa_middleware, layer=0) #otherwise cannot get_block

## 创建 JVCore 合约实例
jvcore_contract = w3.eth.contract(address=jvcore_address, abi=jvcore_abi)

## get id of this node (as audit node)
audit_node_id = w3.geth.admin.node_info().id

## restructure node data
all_peers = w3.geth.admin.peers()
all_connected_ids = functools.reduce(lambda ids, n: ids+[n.id], all_peers, [])

all_nodes = {} #nodes indexed by id
all_miners = {} #miner nodes indexed by lc(signer address)

for node in core_nodes:
    all_nodes[node['id']] = node
    if node['type'] == 'miner':
        all_miners[node['signer'].lower()] = node

    ## add peers in case if not
    if node['id'] == audit_node_id:
        all_nodes[node['id']]['status'] = 'connected'
        all_nodes[node['id']]['type'] = 'witness(a)'
    elif node['id'] in all_connected_ids:
        all_nodes[node['id']]['status'] = 'connected'
    else:
        all_nodes[node['id']]['status'] = 'disconnected'
        print('disconnected. trying to add peer:', node['ip'], node['type'], node['owner'])
        try:
            w3.geth.admin.add_peer(node['enode'])
        except Exception as e:
            print('failed to add peer:', node['ip'], node['type'], node['owner'], str(e))

## update all_miners with information from clique.status
clique_status = w3.provider.make_request('clique_status', [])['result']
for (addr, n) in clique_status['sealerActivity'].items():
    if addr.lower() in all_miners:
        all_miners[addr.lower()]['block_rate'] = n / clique_status['numBlocks']

## get latest block info
last_block_n = w3.eth.get_block_number()
last_block = w3.eth.get_block(last_block_n)
last_block_t = datetime.fromtimestamp(last_block.timestamp)
current_t = datetime.now()
diff_t = current_t - last_block_t

## update all nodes status (miners + witness) and count
count = count_miner = count_witness = 0
for (id, node) in all_nodes.items():
    node_type = node['type']
    if node_type == 'miner':
        node['block_rate'] = all_miners[node['signer'].lower()].get('block_rate') or -1 
        if node['block_rate'] > 0:
            count_miner += 1
            count += 1
    elif node_type == 'miner*':
        node['block_rate'] = 0
    elif node_type in ['witness', 'witness(a)']:
        #node['block_height'] = 0
        # check witness node's rpc 8501 and block height
        ww3 = Web3(Web3.HTTPProvider('http://' + node['ip'] + ':8501'))
        if ww3.is_connected():
            node['block_height'] = ww3.eth.get_block_number()
        else:
            node['block_height'] = 0

        diff_blocks = abs(node['block_height'] - last_block_n)
        if diff_blocks < 10:
            count_witness += 1
            count += 1

## output report
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

## reporting node counts
print('Network Size: ', count, ' nodes (', count_miner, ' miners, ', count_witness, ' witnesses, miner*s excluded)')

## reporting node status
print('---------------- nodes status -----------------')
print('TYPE', 'SINCE', 'IP', 'CONNECTED', 'STATUS', 'ACTIVITY', 'LIVENESS', 'CORE-ID', 'OWNER', 'CHECK-IN')
print('-----------------------------------------------')

no_check_in_list = []
no_kyc_list = []

def formatTokenURI(data_str):
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
        
        # check_in_status = jvcore_contract.functions.isLiveness(core_id).call()
        # check_in_status_display = '👍' if check_in_status else '❌'
        
        check_in_status = False 
        check_in_status_display = '❌' 
        token_info = jvcore_contract.functions.tokenURI(core_id).call()
        if token_info:
            token_info = formatTokenURI(token_info)
            if token_info:
                month_start_timestamp = get_month_start() 
                last_checkin_time = int(token_info['lastCheckInTime'] or 0)
                if last_checkin_time and last_checkin_time > month_start_timestamp:
                    check_in_status = True
                    check_in_status_display = '✅' 
                
        if not check_in_status and node['owner'] not in no_check_in_list:
            no_check_in_list.append(node['owner'])
    else:
        core_id = '--'
        check_in_status_display = '❓'  # 缺失 coreId，显示为未知状态
        if node['owner'] not in no_kyc_list:
            no_kyc_list.append(node['owner'])

    core_id_display = f'J-{core_id}'
    owner_display = f'"{node["owner"]}"'
    print(node['type'], node['since'], node['ip'], enode_connected, node['status'], node_activity, node_liveness, core_id_display, owner_display, check_in_status_display)

## reporting miner status first
for (id, node) in all_nodes.items():
    if node['type'] == 'miner':
        report(node)

## reporting this audit node
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

## optional points recording
score_contract_env = os.environ.get('SCORE_CONTRACT')
audit_send_env = os.environ.get('AUDIT_SEND')
target_date_env = os.environ.get('AUDIT_DATE')
if target_date_env:
    try:
        target_date_int = int(target_date_env)
    except Exception:
        target_date_int = int(datetime.utcnow().strftime('%Y%m%d'))
else:
    biz_dt = datetime.utcnow() + timedelta(hours=8)
    target_date_int = fmt_date_yyyymmdd(biz_dt)
month_start_ts = month_start_ts_utc8_from_chain_ts(int(last_block.timestamp))

per_person = {}
for (_, node) in all_nodes.items():
    core_id = node.get('coreId')
    if core_id is None:
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

    core_ids.append(cid)
    dates.append(int(target_date_int))
    node_types.append(NODE_MINER)
    livenesses.append(bool(entry['minerAlive']))
    checkins.append(bool(is_checkin))
    points.append(int(miner_bp))

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

score_contract_env = score_contract_env or score_contract_default
if audit_send_env != '1':
    print('DRY-RUN: set AUDIT_SEND=1 and SCORE_CONTRACT to enable sending.')
else:
    try:
        audit_points_address = Web3.to_checksum_address(score_contract_env)
    except Exception:
        raise Exception('invalid SCORE_CONTRACT address')
    if len(core_ids) == 0:
        print('No eligible entries to record (missing coreId). Skip sending.')
    else:
        abi_path = os.path.join(os.path.dirname(__file__), 'contracts', 'AuditPoints.abi.json')
        if not os.path.exists(abi_path):
            abi_path = os.path.join(os.path.dirname(__file__), '../contracts/AuditPoints.abi.json')
        with open(abi_path, 'r', encoding='utf-8') as f:
            import json as _json
            full_abi = _json.load(f)
        from_block_env = os.environ.get('FROM_BLOCK')
        to_block_env = os.environ.get('TO_BLOCK')
        from_block = int(from_block_env) if from_block_env else None
        to_block = int(to_block_env) if to_block_env else None
        if dedup_already_recorded(w3, audit_points_address, target_date_int, full_abi, from_block, to_block, sample_ids=list(per_person.keys())):
            print('Dedup: records exist for', target_date_int, 'skip execution (set AUDIT_FORCE=1 to override).')
            if os.environ.get('AUDIT_FORCE') != '1':
                raise SystemExit(0)
        priv = os.environ.get('AUDITOR_PRIVATE_KEY')
        if not priv:
            raise Exception('missing AUDITOR_PRIVATE_KEY environment variable')
        acct = Account.from_key(priv)
        operator_addr = acct.address
        ap_contract = w3.eth.contract(address=audit_points_address, abi=full_abi)
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
                print('Tx failed (likely revert).')
        except Exception as e:
            print('Waiting for receipt failed:', str(e))


