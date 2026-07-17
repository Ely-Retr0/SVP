"""
modules/fingerprint.py
Deep fingerprinting of a single host.
Returns OS guess, open ports, and service/version info.
"""

import nmap

class Fingerprinter:
    def __init__(self):
        self.nm = nmap.PortScanner()

    def probe(self, ip: str) -> dict:
        """
        Run a version + OS detection scan against a single IP.
        Returns a dict with os, ports, and services.
        """
        print(f"[*] Fingerprinting {ip}")
        # -sV: service version detection
        # -O:  OS detection (requires root)
        # -T4: aggressive timing
        # --top-ports 1000: most common ports only (faster)
        self.nm.scan(hosts=ip, arguments="-sV -O -T4 --top-ports 1000")

        result = {
            "ip":       ip,
            "os":       "unknown",
            "ports":    [],
            "services": []
        }

        if ip not in self.nm.all_hosts():
            return result

        host = self.nm[ip]

        # OS detection
        if "osmatch" in host and host["osmatch"]:
            best = host["osmatch"][0]
            result["os"] = f"{best['name']} (accuracy: {best['accuracy']}%)"

        # Open ports and services
        for proto in host.all_protocols():
            for port in host[proto].keys():
                svc = host[proto][port]
                if svc["state"] == "open":
                    entry = {
                        "port":    port,
                        "proto":   proto,
                        "service": svc.get("name", "unknown"),
                        "version": f"{svc.get('product','')} {svc.get('version','')} {svc.get('extrainfo','')}".strip(),
                        "state":   svc["state"]
                    }
                    result["ports"].append(port)
                    result["services"].append(entry)

        print(f"[+] {ip} — OS: {result['os']} | Open ports: {result['ports']}")
        return result
