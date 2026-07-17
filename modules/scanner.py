"""
modules/scanner.py
Host discovery via nmap.
- Active mode  : ping sweep on a given subnet
- Passive mode : listens for 802.11 beacon frames (monitor mode required)
"""

import nmap
import subprocess

class NetworkScanner:
    def __init__(self, interface: str, mode: str = "active"):
        self.interface = interface
        self.mode      = mode
        self.nm        = nmap.PortScanner()

    def scan(self, target: str = None) -> list:
        if self.mode == "passive":
            return self._passive_scan()
        return self._active_scan(target)

    def _active_scan(self, target: str) -> list:
        print(f"[*] Active scan on {target} via {self.interface}")
        self.nm.scan(hosts=target, arguments="-sn")
        hosts = []
        for host in self.nm.all_hosts():
            entry = {
                "ip":       host,
                "mac":      self.nm[host]["addresses"].get("mac", "N/A"),
                "vendor":   "",
                "hostname": self.nm[host].hostname() or "unknown",
                "status":   self.nm[host].state()
            }
            if "vendor" in self.nm[host] and entry["mac"] in self.nm[host]["vendor"]:
                entry["vendor"] = self.nm[host]["vendor"][entry["mac"]]
            hosts.append(entry)
        print(f"[+] Found {len(hosts)} hosts")
        return hosts

    def _passive_scan(self) -> list:
        print(f"[*] Passive scan on {self.interface} for 15s")
        try:
            result = subprocess.run(
                ["sudo", "timeout", "15", "tcpdump", "-i", self.interface,
                 "-e", "type mgt subtype beacon", "-l", "--immediate-mode"],
                capture_output=True, text=True, timeout=20
            )
            seen = {}
            for line in result.stdout.splitlines():
                parts = line.split()
                for i, p in enumerate(parts):
                    if p in ("SA:", "BSSID") and i + 1 < len(parts):
                        bssid = parts[i + 1].rstrip(",")
                        if bssid not in seen:
                            seen[bssid] = {"mac": bssid, "ip": "N/A",
                                           "vendor": "", "hostname": "beacon",
                                           "status": "up"}
            return list(seen.values())
        except Exception as e:
            print(f"[!] Passive scan error: {e}")
            return []
