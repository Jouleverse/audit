import os
import json
from datetime import datetime, timedelta
from web3 import Web3

UTC8_OFFSET_SECS = 8 * 3600
NODE_MINER = 0
NODE_WITNESS = 1

def _load_env_file(path: str):
    import os
    try:
        if not os.path.exists(path):
            return False
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
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

def load_dotenv(cwd_first: bool = True):
    import os
    paths = []
    if cwd_first:
        paths.append(os.path.join(os.getcwd(), '.env'))
        paths.append(os.path.join(os.path.dirname(__file__), '.env'))
    else:
        paths.append(os.path.join(os.path.dirname(__file__), '.env'))
        paths.append(os.path.join(os.getcwd(), '.env'))
    for p in paths:
        if _load_env_file(p):
            break

def load_core_nodes(base_dir: str, override_path: str = None):
    if override_path:
        path = override_path
    else:
        path = os.path.join(base_dir, 'core_nodes.json')
    try:
        # python module support
        if path.endswith('.py'):
            import importlib.util
            spec = importlib.util.spec_from_file_location("core_nodes_config", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            core_nodes = getattr(mod, 'core_nodes')
            if not isinstance(core_nodes, list):
                raise Exception('core_nodes in module is not a list')
            return core_nodes
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise Exception('core_nodes.json format invalid')
            return data
    except Exception as e:
        raise Exception(f'Failed to load core_nodes from {path}: {e}')

def _biz_dt_from_chain_ts(chain_ts: int) -> datetime:
    return datetime.utcfromtimestamp(chain_ts) + timedelta(seconds=UTC8_OFFSET_SECS)

def fmt_date_yyyymmdd(dt: datetime) -> int:
    return int(dt.strftime('%Y%m%d'))

def month_start_ts_utc8_from_chain_ts(chain_ts: int) -> int:
    biz_dt = _biz_dt_from_chain_ts(chain_ts)
    month_start_biz_dt = datetime(biz_dt.year, biz_dt.month, 1)
    month_start_utc_dt = month_start_biz_dt - timedelta(seconds=UTC8_OFFSET_SECS)
    return int(month_start_utc_dt.timestamp())

def role_bp(alive: bool, checkin: bool) -> int:
    if alive and checkin:
        return 100
    elif alive and not checkin:
        return 10
    else:
        return 0

def dedup_already_recorded(w3: Web3, contract_addr: str, target_date: int, abi: list, from_block=None, to_block=None, sample_ids=None):
    try:
        ap_full = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=abi)
        ev_from = from_block if from_block is not None else 0
        ev_to = to_block if to_block is not None else 'latest'
        try:
            logs = ap_full.events.DailyRecorded().get_logs(from_block=ev_from, to_block=ev_to, argument_filters={'date': target_date})
        except TypeError:
            logs = ap_full.events.DailyRecorded().get_logs(fromBlock=ev_from, toBlock=ev_to, argument_filters={'date': target_date})
        if len(logs) > 0:
            return True
        return False
    except Exception:
        try:
            ap_min = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=abi)
            if sample_ids:
                for cid in sample_ids:
                    try:
                        r = ap_min.functions.getCoreDailyRecords(int(cid), target_date).call()
                        if bool(r[0]) or bool(r[4]):
                            return True
                    except Exception:
                        continue
            return False
        except Exception:
            return False
