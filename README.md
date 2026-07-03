# 📡 SVP — Escáner de Vulnerabilidades de Pi

> *A portable Raspberry Pi-based device that scans nearby networks and checks devices against the global CVE vulnerability database — with local AI integration.*

![Status](https://img.shields.io/badge/status-in%20development-dc143c?style=flat-square)
![Hardware](https://img.shields.io/badge/hardware-Raspberry%20Pi-C51A4A?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-39ff14?style=flat-square)

---

## What is SVP?

SVP (Escáner de Vulnerabilidades de Pi) is a portable, self-contained vulnerability scanner built around a **Raspberry Pi** with a wireless antenna module. It passively and actively scans nearby network devices and cross-references them against the **global CVE (Common Vulnerabilities and Exposures) database** to identify potential security weaknesses.

Think of it as a pocket-sized security audit tool.

---

## How It Works

```
[Nearby Devices]
      │
      ▼
[Raspberry Pi + Antenna Module]
      │  scans & fingerprints devices
      ▼
[Device Identification]
  OS, open ports, services, versions
      │
      ▼
[CVE Database Query]
  Match device profile → known CVEs
      │
      ▼
[Report / Alert]
  Vulnerability severity, CVSS score, remediation
      │
      ▼ (optional)
[Local AI — REGO integration]
  Automated analysis & attack path suggestion
```

---

## Features

- 📡 Wireless scanning via external antenna module
- 🔍 Device fingerprinting (OS, services, versions)
- 🗄️ CVE database lookup (NVD API integration)
- 📊 Vulnerability report with CVSS scores
- 🤖 Local AI integration (in development) for automated analysis
- 🔋 Battery-powered, fully portable
- 🖥️ Web dashboard accessible from any device on the local network

---

## Hardware Requirements

| Component | Specification |
|---|---|
| Board | Raspberry Pi 4 (4GB recommended) |
| Antenna | USB wireless adapter (monitor mode capable) |
| Storage | 32GB+ microSD |
| Power | USB-C power bank |
| Case | Optional — portable enclosure |

---

## Software Stack

- **OS:** Raspberry Pi OS Lite / Kali Linux ARM
- **Language:** Python 3
- **Network scanning:** Nmap, Scapy
- **CVE data:** NIST NVD API
- **Dashboard:** Flask / FastAPI
- **AI module:** REGO (local inference)

---

## Quick Start

```bash
git clone https://github.com/Ely-Retr0/SVP
cd SVP
pip install -r requirements.txt
sudo python svp.py --interface wlan1 --scan-range 192.168.1.0/24
```

---

## Roadmap

- [x] Basic network scanner
- [x] CVE database integration
- [ ] Device fingerprinting module
- [ ] Web dashboard
- [ ] Local AI integration
- [ ] Automated report generation (PDF)
- [ ] Bluetooth scanning module

---

## ⚠️ Legal Disclaimer

SVP is designed for **authorized security testing only**. Only scan networks and devices you own or have explicit written permission to test. Unauthorized scanning may be illegal in your jurisdiction.

---

## Author

**Elias Diaz Gutierrez** — [@Ely-Retr0](https://github.com/Ely-Retr0)  
*Think outside the fierrewall*
