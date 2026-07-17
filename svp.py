#!/usr/bin/env python3
"""
SVP — Sandbox Vulnerability Pi
Main entry point. Handles CLI arguments and launches the web dashboard.

Usage:
  sudo python3 svp.py --interface wlan0 --scan-range 192.168.1.0/24
  sudo python3 svp.py --interface wlan1 --mode passive
"""

import argparse
import sys
import os
from flask import Flask, render_template, jsonify, request
from modules.scanner import NetworkScanner
from modules.cve import CVELookup
from modules.fingerprint import Fingerprinter

# ── Argument parsing ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="SVP — Sandbox Vulnerability Pi",
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    "--interface", "-i",
    required=True,
    help="Wireless interface to use (e.g. wlan0, wlan1)"
)
parser.add_argument(
    "--scan-range", "-r",
    default=None,
    help="Target subnet in CIDR notation (e.g. 192.168.1.0/24)"
)
parser.add_argument(
    "--mode", "-m",
    choices=["active", "passive"],
    default="active",
    help="Scan mode:\n  active  — probe hosts directly (requires --scan-range)\n  passive — listen for beacons only (monitor mode required)"
)
parser.add_argument(
    "--port", "-p",
    type=int,
    default=5000,
    help="Port for the web dashboard (default: 5000)"
)
args = parser.parse_args()

if args.mode == "active" and not args.scan_range:
    print("[!] Active mode requires --scan-range. Example: --scan-range 192.168.1.0/24")
    sys.exit(1)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

scanner     = NetworkScanner(interface=args.interface, mode=args.mode)
fingerprint = Fingerprinter()
cve         = CVELookup()

@app.route("/")
def index():
    return render_template("index.html",
                           interface=args.interface,
                           mode=args.mode,
                           scan_range=args.scan_range or "passive")

@app.route("/api/scan", methods=["POST"])
def api_scan():
    """Trigger a scan and return discovered hosts."""
    try:
        hosts = scanner.scan(args.scan_range)
        return jsonify({"ok": True, "hosts": hosts})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/fingerprint", methods=["POST"])
def api_fingerprint():
    """Deep fingerprint a specific host."""
    data = request.get_json()
    ip   = data.get("ip")
    if not ip:
        return jsonify({"ok": False, "error": "ip required"}), 400
    try:
        result = fingerprint.probe(ip)
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/cve", methods=["POST"])
def api_cve():
    """Look up CVEs for a given keyword (vendor, service, version)."""
    data    = request.get_json()
    keyword = data.get("keyword", "")
    count   = data.get("count", 20)
    if not keyword:
        return jsonify({"ok": False, "error": "keyword required"}), 400
    try:
        results = cve.search(keyword, count)
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ── Launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"""
  ╔══════════════════════════════════════╗
  ║   SVP — Sandbox Vulnerability Pi    ║
  ╠══════════════════════════════════════╣
  ║  Interface : {args.interface:<23}║
  ║  Mode      : {args.mode:<23}║
  ║  Range     : {(args.scan_range or 'passive (listen)'):<23}║
  ║  Dashboard : http://0.0.0.0:{args.port:<8}║
  ╚══════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=args.port, debug=False)
