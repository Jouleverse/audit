#!/usr/bin/env python3
import os
import json
import argparse
from datetime import datetime, timedelta
from web3 import Web3

def _month_range(yyyymm: int):
    y = yyyymm // 100
    m = yyyymm % 100
    start = datetime(y, m, 1)
    if m == 12:
        next_start = datetime(y + 1, 1, 1)
    else:
        next_start = datetime(y, m + 1, 1)
    end = next_start - timedelta(days=1)
    return start, end

def _fmt_date_yyyymmdd(dt: datetime) -> int:
    return int(dt.strftime('%Y%m%d'))

def _load_core_ids(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return [int(x) for x in data]

def _load_abi(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

parser = argparse.ArgumentParser('generate_report')
parser.add_argument('--month', help='month YYYYMM', default=datetime.now().strftime('%Y%m'))
parser.add_argument('--ipc', help='path to geth.ipc', default=None)
parser.add_argument('--rpc', help='http rpc url', default=None)
parser.add_argument('--contract', help='AuditPoints address', required=True)
parser.add_argument('--core_ids', help='path to core_ids.json', default=os.path.join(os.path.dirname(__file__), 'core_ids.json'))
parser.add_argument('--abi', help='path to AuditPoints.abi.json', default=os.path.join(os.path.dirname(__file__), '../contracts/AuditPoints.abi.json'))
parser.add_argument('--discover', help='discover coreIds from DailyRecorded events for the month', action='store_true')
parser.add_argument('--jvcore', help='JVCore address for totalSupply traversal', default=None)
parser.add_argument('--cfg', help='config json with jvcore address', default=os.path.join(os.path.dirname(__file__), 'config.json'))
parser.add_argument('--verbose', help='enable verbose logs', action='store_true')
parser.add_argument('--from-events', help='aggregate from events instead of calling per day', action='store_true')
parser.add_argument('--from-block', help='start block for event scan', type=int, default=None)
parser.add_argument('--to-block', help='end block for event scan', type=int, default=None)
args = parser.parse_args()

month_key = int(args.month)
start_dt, end_dt = _month_range(month_key)

if args.rpc:
    w3 = Web3(Web3.HTTPProvider(args.rpc))
else:
    if not args.ipc:
        raise Exception('missing --ipc or --rpc')
    w3 = Web3(Web3.IPCProvider(args.ipc))

if not w3.is_connected():
    raise Exception('web3 not connected')
if args.verbose:
    print('connected')

abi = _load_abi(args.abi)
addr = Web3.to_checksum_address(args.contract)
ap = w3.eth.contract(address=addr, abi=abi)

core_ids = []
try:
    core_ids = _load_core_ids(args.core_ids)
except Exception:
    core_ids = []

def _discover_core_ids(ap, dates):
    s = set()
    for d in dates:
        logs = ap.events.DailyRecorded().get_logs(fromBlock=0, toBlock='latest', argument_filters={'date': d})
        for lg in logs:
            cid = int(lg['args']['coreId'])
            s.add(cid)
    return sorted(list(s))

cores = []
cur = start_dt
dates = []
while cur <= end_dt:
    dates.append(_fmt_date_yyyymmdd(cur))
    cur += timedelta(days=1)
if args.verbose:
    print('month', month_key, 'days', len(dates))

final = {}
core_ids_set = set()

if args.from_events:
    if args.verbose:
        print('scan events')
    ev_from = args.from_block if args.from_block is not None else 0
    ev_to = args.to_block if args.to_block is not None else 'latest'
    rec_logs = []
    ov_logs = []
    for d in dates:
        try:
            rec_logs.extend(ap.events.DailyRecorded().get_logs(from_block=ev_from, to_block=ev_to, argument_filters={'date': d}))
            ov_logs.extend(ap.events.DailyOverridden().get_logs(from_block=ev_from, to_block=ev_to, argument_filters={'date': d}))
        except Exception as e:
            if args.verbose:
                print('log error', d, str(e))
            continue
    def _key(lg):
        return (lg['blockNumber'], lg['logIndex'])
    rec_logs.sort(key=_key)
    ov_logs.sort(key=_key)
    for lg in rec_logs:
        cid = int(lg['args']['coreId'])
        dt = int(lg['args']['date'])
        nt = int(lg['args']['nodeType'])
        l = bool(lg['args']['liveness'])
        c = bool(lg['args']['checkin'])
        p = int(lg['args']['points'])
        final[(cid, nt, dt)] = {"liveness": l, "checkin": c, "points": p}
        core_ids_set.add(cid)
    for lg in ov_logs:
        cid = int(lg['args']['coreId'])
        dt = int(lg['args']['date'])
        nt = int(lg['args']['nodeType'])
        l = bool(lg['args']['newLiveness'])
        c = bool(lg['args']['newCheckin'])
        p = int(lg['args']['newPoints'])
        final[(cid, nt, dt)] = {"liveness": l, "checkin": c, "points": p}
        core_ids_set.add(cid)
    core_ids = sorted(list(core_ids_set))
    if args.verbose:
        print('events', len(rec_logs), len(ov_logs), 'coreIds', len(core_ids))
    if len(core_ids) == 0:
        if args.verbose:
            print('no events found, fallback to JVCore totalSupply traversal')
        args.from_events = False
else:
    if args.discover or len(core_ids) == 0:
        if args.discover:
            core_ids = _discover_core_ids(ap, dates)
            out_discovered = os.path.join(os.path.dirname(__file__), f'core_ids_discovered_{month_key}.json')
            with open(out_discovered, 'w', encoding='utf-8') as f:
                json.dump(core_ids, f, ensure_ascii=False)
        else:
            cfg_addr = None
            if args.jvcore:
                cfg_addr = args.jvcore
            else:
                try:
                    with open(args.cfg, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        cfg_addr = cfg.get('jvcore')
                except Exception:
                    cfg_addr = None
            if not cfg_addr:
                cfg_addr = '0x8d214415b9c5F5E4Cf4CbCfb4a5DEd47fb516392'
            jv_addr = Web3.to_checksum_address(cfg_addr)
            jvcore_abi = [
                {
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            jv = w3.eth.contract(address=jv_addr, abi=jvcore_abi)
            total = int(jv.functions.totalSupply().call())
            core_ids = list(range(0, total))
    if args.verbose:
        print('coreIds', len(core_ids))

for core_id in core_ids:
    if args.verbose:
        print('coreId start', core_id, 'days', len(dates))
    miner_total = 0
    witness_total = 0
    details = []
    for d in dates:
        if args.from_events:
            m = final.get((core_id, 0, d))
            w = final.get((core_id, 1, d))
            minerLiveness = bool(m["liveness"]) if m else False
            minerPoints = int(m["points"]) if m else 0
            witnessLiveness = bool(w["liveness"]) if w else False
            witnessPoints = int(w["points"]) if w else 0
            total = minerPoints + witnessPoints
            if m or w:
                details.append({
                    "date": d,
                    "minerLiveness": minerLiveness,
                    "witnessLiveness": witnessLiveness,
                    "minerPoints": minerPoints,
                    "witnessPoints": witnessPoints,
                    "totalPoints": total
                })
            miner_total += minerPoints
            witness_total += witnessPoints
        else:
            try:
                r = ap.functions.getCoreDailyRecords(core_id, d).call()
            except Exception as e:
                if args.verbose:
                    print('error', core_id, d, str(e))
                continue
            minerExists = bool(r[0])
            minerLiveness = bool(r[1])
            minerPoints = int(r[3])
            witnessExists = bool(r[4])
            witnessLiveness = bool(r[5])
            witnessPoints = int(r[7])
            total = minerPoints + witnessPoints
            if total > 0 or minerExists or witnessExists:
                details.append({
                    "date": d,
                    "minerLiveness": minerLiveness,
                    "witnessLiveness": witnessLiveness,
                    "minerPoints": minerPoints,
                    "witnessPoints": witnessPoints,
                    "totalPoints": total
                })
            miner_total += minerPoints
            witness_total += witnessPoints
    if args.verbose:
        print('coreId done', core_id, 'miner', miner_total, 'witness', witness_total, 'total', int(miner_total + witness_total), 'records', len(details))
    cores.append({
        "coreId": int(core_id),
        "totalPoints": int(miner_total + witness_total),
        "minerTotal": int(miner_total),
        "witnessTotal": int(witness_total),
        "days": len(details),
        "details": details
    })

report = {
    "month": month_key,
    "generatedAt": datetime.now().astimezone().isoformat(),
    "cores": cores
}

dirpath = os.path.dirname(__file__)
out_month = os.path.join(dirpath, f'report_{month_key}.json')
with open(out_month, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False)

out_latest = os.path.join(dirpath, 'report.json')
with open(out_latest, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False)
if args.verbose:
    print('written', out_month, 'and', out_latest)

months_path = os.path.join(dirpath, 'months.json')
months = []
if os.path.exists(months_path):
    try:
        with open(months_path, 'r', encoding='utf-8') as f:
            months = json.load(f)
    except Exception:
        months = []
if month_key not in months:
    months.append(month_key)
months = sorted(months)
with open(months_path, 'w', encoding='utf-8') as f:
    json.dump(months, f, ensure_ascii=False)
print('written', out_month)
