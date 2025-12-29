#!/usr/bin/env python3
import os
import json
import argparse
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware

jvcore_address = "0x8d214415b9c5F5E4Cf4CbCfb4a5DEd47fb516392"
score_contract_default = "0xa1759e40313F07696Bc0F7974EE7454E7C58cc95"

jvcore_abi = [
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

parser = argparse.ArgumentParser("audit_preview_day")
parser.add_argument("--ipc", help="path to geth.ipc", default=None)
parser.add_argument("--rpc", help="http rpc url", default=None)
parser.add_argument("--contract", help="AuditPoints address", default=score_contract_default)
parser.add_argument("--date", help="YYYYMMDD", required=True)
parser.add_argument("--delay", help="seconds between coreId", type=float, default=1.0)
parser.add_argument("--only-positive", help="only show records with exists or points>0", action="store_true")
args = parser.parse_args()

if args.rpc:
    w3 = Web3(Web3.HTTPProvider(args.rpc))
else:
    if not args.ipc:
        raise Exception("missing --ipc or --rpc")
    w3 = Web3(Web3.IPCProvider(args.ipc))
if not w3.is_connected():
    raise Exception("web3 not connected")
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

abi_path = os.path.join(os.path.dirname(__file__), "contracts", "AuditPoints.abi.json")
if not os.path.exists(abi_path):
    abi_path = os.path.join(os.path.dirname(__file__), "../contracts/AuditPoints.abi.json")
with open(abi_path, "r", encoding="utf-8") as f:
    ap_abi = json.load(f)
ap_addr = Web3.to_checksum_address(args.contract)
ap = w3.eth.contract(address=ap_addr, abi=ap_abi)

jv = w3.eth.contract(address=Web3.to_checksum_address(jvcore_address), abi=jvcore_abi)
total = int(jv.functions.totalSupply().call())

date_int = int(args.date)
for cid in range(0, total):
    try:
        r = ap.functions.getCoreDailyRecords(cid, date_int).call()
    except Exception as e:
        print("error", cid, date_int, str(e))
        time.sleep(args.delay)
        continue
    minerExists = bool(r[0])
    minerLiveness = bool(r[1])
    minerPoints = int(r[3])
    witnessExists = bool(r[4])
    witnessLiveness = bool(r[5])
    witnessPoints = int(r[7])
    totalPoints = minerPoints + witnessPoints
    if args.only_positive:
        if not (minerExists or witnessExists or totalPoints > 0):
            time.sleep(args.delay)
            continue
    print("J-%d" % cid, "date", date_int, "miner", int(minerLiveness), minerPoints, "witness", int(witnessLiveness), witnessPoints, "total", totalPoints)
    time.sleep(args.delay)
