"""
modules/cve.py
CVE lookup against the NIST NVD API v2.
No API key required. Rate limited to ~5 req/30s by NVD.
"""

import requests
import time

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

class CVELookup:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._last_request = 0

    def _rate_limit(self):
        """NVD allows ~5 requests per 30 seconds without API key."""
        elapsed = time.time() - self._last_request
        if elapsed < 6:
            time.sleep(6 - elapsed)
        self._last_request = time.time()

    def search(self, keyword: str, count: int = 20) -> list:
        """
        Search NVD for CVEs matching a keyword.
        Returns a list of CVE dicts ordered by CVSS score descending.
        """
        self._rate_limit()
        print(f"[*] CVE lookup: '{keyword}' (max {count})")

        params = {
            "keywordSearch":  keyword,
            "resultsPerPage": min(count, 50),
            "startIndex":     0
        }

        try:
            resp = self.session.get(NVD_API, params=params, timeout=15)
            resp.raise_for_status()
            data  = resp.json()
            vulns = data.get("vulnerabilities", [])
            total = data.get("totalResults", 0)
            print(f"[+] {total} CVEs found for '{keyword}'")
            return [self._parse(v) for v in vulns]

        except requests.exceptions.Timeout:
            print("[!] NVD API timeout")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[!] NVD API error: {e}")
            return []

    def _parse(self, item: dict) -> dict:
        """Extract the fields we care about from a raw NVD CVE entry."""
        cve  = item.get("cve", {})
        desc = next(
            (d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"),
            "No description available."
        )
        score, severity, vector = self._extract_cvss(cve.get("metrics", {}))

        return {
            "id":          cve.get("id", "N/A"),
            "description": desc,
            "score":       score,
            "severity":    severity,
            "vector":      vector,
            "published":   cve.get("published", "")[:10],
            "modified":    cve.get("lastModified", "")[:10],
            "references":  len(cve.get("references", [])),
            "url":         f"https://nvd.nist.gov/vuln/detail/{cve.get('id','')}"
        }

    def _extract_cvss(self, metrics: dict) -> tuple:
        """Return (score, severity, vector) from whichever CVSS version is available."""
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if key in metrics and metrics[key]:
                m      = metrics[key][0]
                data   = m.get("cvssData", {})
                score  = data.get("baseScore")
                vector = data.get("vectorString", "")
                sev    = self._score_to_severity(score)
                return score, sev, vector
        return None, "N/A", ""

    @staticmethod
    def _score_to_severity(score) -> str:
        if score is None:
            return "N/A"
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        return "LOW"
