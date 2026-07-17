#  SVP — Sandbox Vulnerability Pi

> *A portable Raspberry Pi-based network scanner that fingerprints nearby devices and cross-references them against the global CVE vulnerability database.*

![Status](https://img.shields.io/badge/status-active-39ff14?style=flat-square)
![Hardware](https://img.shields.io/badge/Raspberry%20Pi%20OS%20v.4-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)
![OS](https://img.shields.io/badge/Debian%2012-A81D33?style=flat-square&logo=debian&logoColor=white)
![Python](https://img.shields.io/badge/Python%203-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-00599C?style=flat-square)

---

## What is SVP?

**SVP (Sandbox Vulnerability Pi)** is a self-contained, portable network security scanner built on a Raspberry Pi 4. It scans nearby networks, fingerprints discovered devices (OS, open ports, running services and their versions), and cross-references that data against the **NIST NVD CVE database** to surface known vulnerabilities with their CVSS severity scores — all through a clean web dashboard accessible from your phone or laptop.

Think of it as a pocket-sized security audit tool you can carry anywhere.

> **Important:** SVP has two distinct operating modes depending on your hardware. Understanding which mode fits your use case is the most important decision before building this. Both are documented in full below.

---

##  Project Structure

```
SVP/
├── svp.py                  # Main entry point — CLI + Flask server
├── requirements.txt        # Python dependencies
├── modules/
│   ├── scanner.py          # Host discovery (active + passive)
│   ├── fingerprint.py      # Deep OS + service detection per host
│   └── cve.py              # NIST NVD API v2 CVE lookup
├── templates/
│   └── index.html          # Web dashboard HTML
└── static/
    ├── css/style.css        # Dashboard styles
    └── js/app.js            # Dashboard frontend logic
```

---

## Operating Modes

SVP can run in two fundamentally different modes. The difference comes down to one thing: **whether `wlan0` is free to scan, or busy emitting a Wi-Fi network.**

---

### Mode A — Integrated Antenna (Single Adapter)

**What it means:** The Pi's built-in `wlan0` connects to an existing Wi-Fi network and scans devices on that same network from the inside.

```
Your Router / Network
        │
        │  wlan0 (connected as client)
        ▼
  Raspberry Pi
        │  scans subnet
        ▼
  All devices on the network
  (laptops, phones, IoT, smart TVs...)
        │
        ▼
  CVE lookup → vulnerability report
  Dashboard: http://<Pi IP>:5000
```

**When this makes sense:**
- You want to audit your own home or office network
- You want a quick setup without extra hardware
- You're okay joining the target network first

**Limitation:** Can only see devices on the network it joined. Cannot operate standalone.

---

### Mode B — External USB Antenna (Dual Adapter) ⭐ Recommended

**What it means:** Two wireless interfaces work simultaneously:
- `wlan0` (built-in) — emits its own isolated AP so you can SSH in wirelessly without any external router
- `wlan1` (USB adapter) — dedicated to scanning, with monitor mode support for passive discovery

```
[Target Network / Environment]
        │
        │  wlan1 (USB — scanning / monitor mode)
        ▼
  Raspberry Pi ◄──── SSH via wlan0 AP (10.3.141.1)
        │                    ▲
        ▼              Your Laptop
  Fingerprinting
        │
        ▼
  CVE lookup → report
  Dashboard: http://10.3.141.1:5000
```

**When this makes sense:**
- You want the Pi to be 100% self-contained (no dependency on any router)
- You want to scan a network without being visibly connected to it as a client
- You're using the Pi as a drop device — left somewhere, scanning autonomously
- You already have the [SPS lab](https://github.com/Ely-Retr0/SPS) setup and want scanning on top

**Why this is recommended:** You SSH into the Pi through its own AP while `wlan1` does the actual work. The Pi never needs to "join" anything — it just listens and probes.

---

## 🔍 How It Works — The Pipeline

Once SVP has network access, every scan follows this pipeline:

```
Step 1 — Host Discovery
  nmap -sn <subnet>
  → Find which IPs are alive

Step 2 — Port & Service Scan
  nmap -sV -O <target IP>
  → Open ports, service names, version strings, OS guess

Step 3 — Device Fingerprinting
  Parse nmap output → extract:
    • Vendor (from MAC OUI)
    • OS family and version
    • Service + version string per port

Step 4 — CVE Lookup
  GET https://services.nvd.nist.gov/rest/json/cves/2.0
      ?keywordSearch=<vendor + service + version>
  → Matching CVEs with CVSS scores, descriptions, references

Step 5 — Dashboard
  Results rendered in the browser:
    • Per-device card with all open ports
    • CVE list ordered by severity (Critical → Low)
    • Click any CVE ID → opens NVD entry directly
```

---

## Hardware Requirements

| Component | Mode A | Mode B |
|---|---|---|
| Board | Raspberry Pi 4 (4GB+ RAM) | Raspberry Pi 4 (4GB+ RAM) |
| Built-in WiFi | Used to connect to target network | Used to emit the AP (10.3.141.1) |
| USB WiFi Adapter | Not needed | **Required** — must support monitor mode |
| Recommended adapter | — | Alfa AWUS036ACH (RTL8812AU) or TP-Link TL-WN722N v1 (AR9271) |
| Storage | 32GB+ microSD | 32GB+ microSD |
| Power | USB-C power bank | USB-C power bank |

> ⚠️ **Monitor mode note:** Most cheap USB adapters do NOT support monitor mode. Always verify the chipset before buying. The RTL8812AU and AR9271 are the most widely supported on Debian/Pi OS.

---

## Installation

### 1. System dependencies

```bash
sudo apt update && sudo apt install -y \
  nmap \
  python3 \
  python3-pip \
  tcpdump \
  aircrack-ng
```

### 2. Clone and install

```bash
git clone https://github.com/Ely-Retr0/SVP
cd SVP
pip3 install -r requirements.txt --break-system-packages
```

### 3. (Mode B only) Put the USB adapter into monitor mode

```bash
# Confirm both interfaces are visible
ip link show

# Put wlan1 into monitor mode
sudo ip link set wlan1 down
sudo iw dev wlan1 set type monitor
sudo ip link set wlan1 up

# Verify
iwconfig wlan1
# Should show: Mode:Monitor
```

---

## Usage

```bash
# Mode A — active scan via built-in adapter
sudo python3 svp.py --interface wlan0 --scan-range 192.168.1.0/24

# Mode B — active scan via USB adapter
sudo python3 svp.py --interface wlan1 --scan-range 192.168.1.0/24

# Mode B — passive beacon discovery (monitor mode required, no subnet needed)
sudo python3 svp.py --interface wlan1 --mode passive

# Custom dashboard port
sudo python3 svp.py --interface wlan1 --scan-range 192.168.1.0/24 --port 8888
```

**Access the dashboard:**

| Mode | URL |
|---|---|
| Mode A | `http://<Pi's IP on the network>:5000` |
| Mode B | `http://10.3.141.1:5000` (via Pi's own AP) |

---

## Web Dashboard

The dashboard has three sequential panels:

**[ 01 ] HOST DISCOVERY** — Hit *Run Scan* to discover all live hosts on the subnet. Each host card shows IP, MAC, vendor, and hostname.

**[ 02 ] FINGERPRINT** — Click *Fingerprint* on any host card to run a deep OS + service version scan on that specific device.

**[ 03 ] CVE LOOKUP** — After fingerprinting, the most relevant service is pre-filled automatically. Hit *Search NVD* to query the vulnerability database. Results show CVSS score, severity badge, description, and a direct link to the NVD entry.

---

## Software Stack

| Layer | Tool |
|---|---|
| OS | Raspberry Pi OS / Debian 12 ARM64 |
| Network scanning | Nmap |
| Monitor mode | Aircrack-ng + tcpdump |
| CVE data | NIST NVD API v2 (no API key required) |
| Backend | Python 3 + Flask |
| Frontend | HTML / CSS / Vanilla JS |

---


## Roadmap

- [x] Host discovery (active + passive)
- [x] Service + OS fingerprinting
- [x] CVE database integration (NVD API v2)
- [x] Web dashboard
- [ ] PDF report generation
- [ ] Bluetooth scanning module
- [ ] Scheduled / continuous scanning with alerting
- [ ] Local AI integration for automated analysis

---

## SPS Integration

SVP is designed to work alongside **[SPS — Sandbox Pentest Server](https://github.com/Ely-Retr0/SPS)** — the companion project that runs DVWA, Juice Shop, and MariaDB as Docker containers on the same Pi.

Together they form a complete pentesting ecosystem:
AP: RaspAP (10.3.141.1)
│
├── :9000  Portainer    → container management
├── :5000  SVP          → network scanner + CVE lookup
├── :8080  DVWA         → vulnerable target
└── :3000  Juice Shop   → vulnerable target

### Option A — Run SVP as a Docker container inside SPS

The cleanest integration. SVP runs as just another container in the lab, accessible at `http://10.3.141.1:5000` alongside the other services.

**1. Add this `Dockerfile` to the root of the SVP repo:**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    nmap \
    tcpdump \
    aircrack-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "svp.py", "--interface", "eth0", "--scan-range", "10.3.141.0/24"]
```

**2. Build and deploy:**

```bash
docker build -t svp .

docker run -d \
  --name lab-svp \
  --network lab-net \
  -p 5000:5000 \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --restart always \
  svp
```

> `--cap-add NET_ADMIN` and `--cap-add NET_RAW` are required so nmap can send raw packets from inside the container.

---

### Option B — Use SVP to scan your own SPS lab containers

The most educational use case. Point SVP at the internal Docker network (`lab-net`) and scan your own vulnerable targets exactly like you would a real network.

```bash
# Get the lab-net subnet (run this on the Pi)
docker network inspect lab-net | grep Subnet
# Usually: 172.18.0.0/16

# Scan your own lab
sudo python svp.py --interface eth0 --scan-range 172.18.0.0/16
```

What you'll see in the dashboard:

| IP | Container | Service | Use case |
|---|---|---|---|
| 172.18.0.2 | lab-db | MariaDB :3306 | Find DB CVEs |
| 172.18.0.3 | lab-dvwa | Apache :80 | SQLi, XSS practice |
| 172.18.0.4 | lab-juiceshop | Node.js :3000 | Modern web app attacks |

**The full practice loop:**
SVP scan → discover services
│
▼
CVE lookup → find known vulnerabilities
│
▼
Exploit manually → DVWA / Juice Shop
│
▼
Understand what each CVE means in practice

This is the closest you can get to a real engagement without touching anything you don't own.

---


## Legal Disclaimer

SVP is designed **strictly for authorized security testing and educational research**.

Only scan networks and devices you own or have **explicit written permission** to test. Unauthorized network scanning may be illegal in your jurisdiction. The author assumes no responsibility for misuse of this tool.

---

## Author

**Elias Diaz Gutierrez** — [@Ely-Retr0](https://github.com/Ely-Retr0)

*Think outside the fierrewall.*

---

>  **Want the full isolated pentesting lab this scanner pairs with?**
> Check out **[SPS — Sandbox Pentest Server](https://github.com/Ely-Retr0/SPS)** — the companion project that turns a Raspberry Pi into a self-contained lab with DVWA, Juice Shop, and Docker orchestration.
