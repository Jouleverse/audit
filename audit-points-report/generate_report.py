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

abi = _load_abi(args.abi)
addr = Web3.to_checksum_address(args.contract)
ap = w3.eth.contract(address=addr, abi=abi)

core_ids = _load_core_ids(args.core_ids)

cores = []
cur = start_dt
dates = []
while cur <= end_dt:
    dates.append(_fmt_date_yyyymmdd(cur))
    cur += timedelta(days=1)

for core_id in core_ids:
    miner_total = 0
    witness_total = 0
    details = []
    for d in dates:
        r = ap.functions.getCoreDailyRecords(core_id, d).call()
        minerExists = bool(r[0])
        minerLiveness = bool(r[1])
        minerCheckin = bool(r[2])
        minerPoints = int(r[3])
        witnessExists = bool(r[4])
        witnessLiveness = bool(r[5])
        witnessCheckin = bool(r[6])
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
