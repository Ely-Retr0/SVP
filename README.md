#  SVP — Sandbox Vulnerability Pi

> *A portable Raspberry Pi-based network scanner that fingerprints nearby devices and cross-references them against the global CVE vulnerability database.*

![Status](https://img.shields.io/badge/status-active-39ff14?style=flat-square)
![Hardware](https://img.shields.io/badge/Raspberry%20Pi%204-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)
![OS](https://img.shields.io/badge/Debian%2012-A81D33?style=flat-square&logo=debian&logoColor=white)
![Python](https://img.shields.io/badge/Python%203-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-00599C?style=flat-square)

---

##  What is SVP?

**SVP (Sandbox Vulnerability Pi)** is a self-contained, portable network security scanner built on a Raspberry Pi 4. It scans nearby networks, fingerprints discovered devices (OS, open ports, running services and their versions), and cross-references that data against the **NIST NVD CVE database** to surface known vulnerabilities with their CVSS severity scores.

Think of it as a pocket-sized security audit tool you can carry anywhere.

> **Honest note:** SVP has two distinct operating modes depending on your hardware. Understanding which mode fits your use case is the most important decision before building this. Both are documented in full below.

---

##  Operating Modes

SVP can run in two fundamentally different modes. The difference comes down to one thing: **whether `wlan0` is free to scan, or busy emitting a Wi-Fi network.**

---

### Mode A — Integrated Antenna (Single Adapter)

**What it means:** The Pi's built-in `wlan0` is used for everything. It connects to an existing Wi-Fi network (your home router, a hotspot, etc.) and scans devices on that same network from the inside.

**Real-world flow:**
```
Your Router / Network
        │
        │  wlan0 (connected as client)
        ▼
  Raspberry Pi
        │  scans 192.168.X.0/24
        ▼
  Devices on the same network
  (laptops, phones, IoT, printers...)
        │
        ▼
  CVE lookup → vulnerability report
```

**When this makes sense:**
- You want to audit your own home network
- You want a quick scan without extra hardware
- You're okay connecting the Pi to the target network first

**Limitations:**
- Can only see devices on the network it's connected to
- Cannot scan networks it hasn't joined
- Cannot operate in full isolation (depends on an external router)

**Setup:**

```bash
# Connect Pi to your network (if not already)
sudo nmcli dev wifi connect "YourSSID" password "YourPassword"

# Verify connection and get your subnet
ip addr show wlan0
# Note the IP, e.g. 192.168.1.45 → your subnet is 192.168.1.0/24

# Install dependencies
sudo apt update && sudo apt install nmap python3-pip -y
pip3 install requests python-nmap --break-system-packages

# Clone the project
git clone https://github.com/Ely-Retr0/SVP
cd SVP

# Run a scan against your subnet
sudo python3 svp.py --interface wlan0 --scan-range 192.168.1.0/24
```

**Access the dashboard** from any device on the same network:
```
http://<Pi's IP>:5000
```

---

### Mode B — External USB Antenna (Dual Adapter) ⭐ Recommended

**What it means:** The Pi uses two wireless interfaces simultaneously:
- `wlan0` (built-in) — keeps emitting its own isolated AP (from the SPS lab setup), so you can SSH in wirelessly without needing any external router
- `wlan1` (USB adapter) — dedicated to scanning external networks, with monitor mode support for passive scanning

**Real-world flow:**
```
[External Networks / Target Environment]
        │
        │  wlan1 (USB adapter — scanning / monitor mode)
        ▼
  Raspberry Pi ←──── SSH via wlan0 AP (10.3.141.1)
        │                    ▲
        │              Your Laptop
        ▼
  Device fingerprinting
        │
        ▼
  CVE lookup → vulnerability report
        │
        ▼
  Dashboard at http://10.3.141.1:5000
```

**When this makes sense:**
- You want the Pi to be fully self-contained (no dependency on any external router)
- You want to scan a network without being visibly connected to it as a client
- You're using the Pi as a drop device — hidden somewhere, scanning autonomously
- You already have the SPS lab setup and want to add scanning on top

**Why this is the recommended mode:** You SSH into the Pi through its own AP (`wlan0`), while `wlan1` does the actual work on the target network. The Pi never needs to "join" anything — it just listens and probes.

**Hardware needed:**

| Component | Specification |
|---|---|
| USB WiFi Adapter | Must support **monitor mode** |
| Recommended chipsets | Alfa AWUS036ACH (RTL8812AU), TP-Link TL-WN722N v1 (AR9271) |
| Avoid | Most cheap adapters — verify chipset before buying |

**Setup:**

```bash
# Connect to the Pi via its own AP
ssh admin@10.3.141.1

# Plug in the USB adapter and verify it appears
ip link show
# You should see wlan0 (built-in AP) and wlan1 (USB adapter)

# Install aircrack-ng suite for monitor mode support
sudo apt update && sudo apt install aircrack-ng nmap python3-pip -y
pip3 install requests python-nmap --break-system-packages

# Put wlan1 into monitor mode
sudo ip link set wlan1 down
sudo iw dev wlan1 set type monitor
sudo ip link set wlan1 up

# Verify monitor mode is active
iwconfig wlan1
# Should show: Mode:Monitor

# Clone the project
git clone https://github.com/Ely-Retr0/SVP
cd SVP

# Run a passive scan (discover nearby networks)
sudo python3 svp.py --interface wlan1 --mode passive

# Run an active scan against a specific subnet
sudo python3 svp.py --interface wlan1 --scan-range 192.168.1.0/24
```

**Access the dashboard** through the Pi's own AP:
```
http://10.3.141.1:5000
```

---

##  How Scanning Works

Regardless of mode, SVP follows the same pipeline once it has network access:

```
Step 1 — Host Discovery
  nmap -sn <subnet>
  → Find which IPs are alive on the network

Step 2 — Port & Service Scan
  nmap -sV -O <target IP>
  → Identify open ports, running services, version numbers, OS

Step 3 — Device Fingerprinting
  Parse nmap output → extract:
    • Vendor (from MAC OUI lookup)
    • OS family and version
    • Service name + version string

Step 4 — CVE Lookup
  Query NIST NVD API v2:
  GET https://services.nvd.nist.gov/rest/json/cves/2.0
      ?keywordSearch=<vendor + service + version>
  → Returns matching CVEs with CVSS scores

Step 5 — Report Generation
  For each device:
    • List of CVEs ordered by severity (Critical → Low)
    • CVSS score, description, publication date
    • Direct link to NVD entry for remediation details
```

---

##  Web Dashboard

SVP exposes a local web dashboard accessible from any device connected to the same network (or to the Pi's AP in Mode B).

| Feature | Description |
|---|---|
| Live scan trigger | Start a scan from the browser |
| Device list | All discovered hosts with vendor info |
| CVE results | Per-device vulnerability list with CVSS badges |
| Severity filter | Filter by Critical / High / Medium / Low |
| NVD deep link | Click any CVE ID to open its full NVD entry |

---

##  Software Stack

| Layer | Tool |
|---|---|
| OS | Debian 12 ARM64 |
| Network scanning | Nmap, Scapy |
| Monitor mode | Aircrack-ng suite |
| CVE data | NIST NVD API v2 (no API key required) |
| Backend | Python 3 + Flask |
| Frontend | Vanilla HTML/CSS/JS (no frameworks) |

---

##  Quick Start

```bash
git clone https://github.com/Ely-Retr0/SVP
cd SVP
pip3 install -r requirements.txt --break-system-packages

# Mode A — integrated antenna
sudo python3 svp.py --interface wlan0 --scan-range 192.168.1.0/24

# Mode B — external USB antenna
sudo python3 svp.py --interface wlan1 --scan-range 192.168.1.0/24

# Passive network discovery (Mode B only, monitor mode required)
sudo python3 svp.py --interface wlan1 --mode passive
```

---

##  Roadmap

- [x] Basic network scanner
- [x] CVE database integration (NVD API v2)
- [x] Device fingerprinting module
- [x] Web dashboard
- [ ] Automated PDF report generation
- [ ] Bluetooth scanning module
- [ ] Local AI integration for automated analysis
- [ ] Scheduled/continuous scanning with alerting

---

## ⚠️ Legal Disclaimer

SVP is designed **strictly for authorized security testing and educational research**.

Only scan networks and devices you own or have **explicit written permission** to test. Unauthorized network scanning may be illegal in your jurisdiction. The author assumes no responsibility for misuse of this tool.

---

##  Author

**Elias Diaz Gutierrez** — [@Ely-Retr0](https://github.com/Ely-Retr0)

*Think outside the fierrewall.*

---

> 💡 **Building the isolated lab environment this scanner is based on?** Check out **[SPS — Sandbox Pentest Server](https://github.com/Ely-Retr0/SPS)** — the companion project that turns a Raspberry Pi into a fully self-contained pentesting lab.
