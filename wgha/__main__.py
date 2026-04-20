#!/usr/bin/env python3

from subprocess import Popen, PIPE
from argparse import ArgumentParser
import configparser
import json
import logging
import os
import requests
import sys
import time

cparser = configparser.ConfigParser()

COMMAND_PREFIX = "docker exec wireguard".split(" ")

def load_config(config_path):
    if not config_path or not os.path.exists(config_path):
        return {}
    # Only support INI
    parser = configparser.ConfigParser()
    parser.read(config_path)
    # Flatten to dict
    return {k: dict(v) for k, v in parser.items()}

# Argument parsing for logfile, token file, baseurl, and config
parser = ArgumentParser(
    description="Update Home Assistant with WireGuard connection status."
)
parser.add_argument("token_file", help="Path to Home Assistant token file")
parser.add_argument(
    "--baseurl",
    default=None,
    help="Home Assistant API base URL (default: http://192.168.0.97:8123/api or config file)",
)
parser.add_argument(
    "--logfile", default="wgha.log", help="Log file path (default: wgha.log)"
)
parser.add_argument(
    "--config", default=None, help="Optional config file (INI) for persistent settings"
)
args = parser.parse_args()

# Set up logging
logging.basicConfig(
    filename=args.logfile,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

# Load config file if provided
config = {}
if args.config:
    try:
        config = load_config(args.config)
        logging.info(f"Loaded config from {args.config}")
    except Exception as e:
        logging.error(f"Failed to load config file {args.config}: {e}")
        sys.exit(1)

# Determine baseurl (priority: CLI > config > default)
baseurl = args.baseurl or config.get("baseurl")
if not baseurl:
    logging.error(
        "Home Assistant baseurl must be provided via --baseurl or config file."
    )
    sys.exit(1)

TOKEN_FILE = args.token_file
if not os.path.exists(TOKEN_FILE):
    logging.error(f"Token file does not exist: {TOKEN_FILE}")
    sys.exit(1)
try:
    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()
except Exception as e:
    logging.error(f"Failed to read token file {TOKEN_FILE}: {e}")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

def remoteExec(params):
    process = Popen(COMMAND_PREFIX + params, stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    return output.decode()

def getKnownClients():
    directories = remoteExec(["ls", "/config"]).split("\n")
    # filter only tje ones prefixed by peer_
    peer_names = [x for x in directories if "peer_" in x]

    peer_details = []

    for n in peer_names:
        confstring = remoteExec(["cat", f"/config/{n}/{n}.conf"])
        # print(confstring)
        cparser.read_string(confstring)
        conf_item = {"name": n, "address": cparser["Interface"]["Address"]}
        peer_details.append(conf_item)
    return peer_details

def getConnectionInto():
    details = remoteExec(["wg", "show", "all", "dump"]).strip().split("\n")
    if not details or len(details) < 1:
        return {}

    result = {}
    i = 0
    while i < len(details):
        fields = details[i].split("\t")
        if len(fields) == 5:
            # Device line: device, private_key, public_key, listen_port, fwmark
            device, private_key, public_key, listen_port, fwmark = fields
            result[device] = {}
            if private_key != "(none)":
                result[device]["privateKey"] = private_key
            if public_key != "(none)":
                result[device]["publicKey"] = public_key
            if listen_port != "0":
                result[device]["listenPort"] = int(listen_port)
            if fwmark != "off":
                result[device]["fwmark"] = int(fwmark)
            result[device]["peers"] = {}
            i += 1
        elif len(fields) == 9:
            # Peer line
            (
                device,
                public_key,
                preshared_key,
                endpoint,
                allowed_ips,
                latest_handshake,
                transfer_rx,
                transfer_tx,
                persistent_keepalive,
            ) = fields
            peer = {}
            if preshared_key != "(none)":
                peer["presharedKey"] = preshared_key
            if endpoint != "(none)":
                peer["endpoint"] = endpoint
            if latest_handshake != "0":
                peer["latestHandshake"] = int(latest_handshake)
            if transfer_rx != "0":
                peer["transferRx"] = int(transfer_rx)
            if transfer_tx != "0":
                peer["transferTx"] = int(transfer_tx)
            if persistent_keepalive != "off":
                peer["persistentKeepalive"] = int(persistent_keepalive)
            # allowedIps is a comma-separated list
            if allowed_ips != "(none)":
                peer["allowedIps"] = [ip for ip in allowed_ips.split(",") if ip]
            else:
                peer["allowedIps"] = []

            result[device]["peers"][public_key] = peer
            i += 1
        else:
            i += 1
    return result

def map_names_to_allowed_ips(clients, connections):
    def base(ip):
        return ip.split("/")[0] if ip else ip

    ip_map = {}
    for device, info in connections.items():
        for pubkey, peer in info.get("peers", {}).items():
            for allowed in peer.get("allowedIps", []):
                ip_map[base(allowed)] = peer

    result = {}
    for peer in clients:
        if peer["address"] not in ip_map.keys():
            continue

        result[peer["name"]] = {
            "address": peer["address"],
            "connection": ip_map[peer["address"]],
        }
    return result

if __name__ == "__main__":
    logging.info("Starting WireGuard-HomeAssistant status update.")
    p = getKnownClients()
    d = getConnectionInto()
    mapping = map_names_to_allowed_ips(p, d)

    connected = {}
    for peer, details in mapping.items():
        result = False
        if "latestHandshake" in details["connection"].keys():
            if time.time() - details["connection"]["latestHandshake"] < 10 * 60:
                result = True
        connected[peer] = result

    logging.info("Connection status: %s", json.dumps(connected, indent=2))

    for name, value in connected.items():
        action = "turn_off"
        if value:
            action = "turn_on"

        data = {
            "entity_id": f"input_boolean.{name}",
        }

        try:
            response = requests.post(
                f"{baseurl}/services/input_boolean/{action}", headers=headers, json=data
            )
            logging.info(f"Updated {name}: {action}, response: {response.content}")
        except Exception as e:
            logging.error(f"Failed to update {name}: {e}")

"""
input_boolean:
  peer_starvpnjune:
    name: peer_starvpnjune
  peer_starvpnmark:
    name: peer_starvpnmark
  peer_starz7070:
    name: peer_starz7070
  peer_starzs23:
    name: peer_starzs23
  peer_starztab:
    name: peer_starztab
  peer_starztower:
    name: peer_starztower
  peer_starzvpnpax:
    name: peer_starzvpnpax
  peer_starzvpnbrooke:
    name: peer_starzvpnbrooke
  peer_starzvpnlucy:
    name: peer_starzvpnlucy
"""
