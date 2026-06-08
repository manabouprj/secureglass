"""
SentinelOne-Glass — Demo Data Generator
Generates realistic synthetic security alerts across 20 controls
for GitHub demo purposes. No real vendor credentials required.
"""

import json
import random
import uuid
from datetime import datetime, timedelta, timezone

TOOLS = [
    "crowdstrike", "mimecast", "qualys", "zscaler", "palo_alto",
    "wiz", "axonius", "sentinel_siem", "salt_security", "recorded_future",
    "symantec_dlp", "vectra_ai", "cyberark", "extrahop", "cloudflare_waf",
    "prisma_cloud", "intune", "veeam", "knowbe4", "darktrace"
]

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
SEVERITY_WEIGHTS = [0.05, 0.15, 0.40, 0.30, 0.10]

CATEGORIES = [
    "ENDPOINT", "EMAIL", "VULNERABILITY", "NETWORK", "CLOUD",
    "IDENTITY", "DLP", "API", "BRAND", "AI_THREAT"
]

REGIONS = [
    "AE", "GB", "US", "DE", "SG", "ZA", "BR", "IN",
    "FR", "JP", "AU", "CA", "NL", "SE", "NG", "KE"
]
REGION_WEIGHTS = [0.15, 0.12, 0.12, 0.08, 0.07, 0.06, 0.06, 0.06,
                  0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02]

CLOUDS = ["azure", "aws", "gcp", "on-prem", "saas"]
CLOUD_WEIGHTS = [0.35, 0.30, 0.15, 0.15, 0.05]

MITRE_TACTICS = [
    "Initial Access", "Execution", "Persistence", "Privilege Escalation",
    "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
    "Collection", "Command and Control", "Exfiltration", "Impact"
]

SAMPLE_ALERTS = {
    "crowdstrike": [
        ("Falcon sensor detected Mimikatz credential dumping tool",
         "CRITICAL", "T1003.001", "Credential Access"),
        ("Ransomware-like behaviour detected: mass file encryption",
         "CRITICAL", "T1486", "Impact"),
        ("Cobalt Strike beacon communication detected",
         "HIGH", "T1071.001", "Command and Control"),
        ("PowerShell encoded command execution from Office process",
         "HIGH", "T1059.001", "Execution"),
        ("LSASS memory access by non-system process",
         "HIGH", "T1003.001", "Credential Access"),
        ("Suspicious lateral movement via SMB detected",
         "MEDIUM", "T1021.002", "Lateral Movement"),
        ("New service installation in unusual path",
         "MEDIUM", "T1543.003", "Persistence"),
    ],
    "mimecast": [
        ("Malicious attachment blocked: invoice.xlsm with VBA macro",
         "HIGH", "T1566.001", "Initial Access"),
        ("CEO impersonation email intercepted — wire fraud attempt",
         "CRITICAL", "T1566.002", "Initial Access"),
        ("Phishing URL click blocked: credential harvesting page",
         "HIGH", "T1566.002", "Initial Access"),
        ("Bulk spam campaign targeting finance department",
         "MEDIUM", "T1566.001", "Initial Access"),
        ("Malware-laden PDF attachment quarantined",
         "HIGH", "T1566.001", "Initial Access"),
    ],
    "qualys": [
        ("Critical CVE-2024-3400 (PAN-OS) detected on 12 firewalls",
         "CRITICAL", "T1190", "Initial Access"),
        ("Log4Shell (CVE-2021-44228) still unpatched on 3 Java servers",
         "HIGH", "T1190", "Initial Access"),
        ("ProxyNotShell Exchange vulnerability on 2 mail servers",
         "HIGH", "T1190", "Initial Access"),
        ("47 systems with high-severity patches overdue >30 days",
         "HIGH", "T1195", "Initial Access"),
        ("EOL Windows Server 2012 R2 detected: 8 instances",
         "HIGH", "T1195", "Initial Access"),
        ("SSL certificate expiry in <7 days on 3 public endpoints",
         "MEDIUM", "T1600", "Defense Evasion"),
    ],
    "wiz": [
        ("Publicly exposed S3 bucket with PII data detected",
         "CRITICAL", "T1530", "Collection"),
        ("Azure VM with public IP and no NSG running deprecated OS",
         "HIGH", "T1190", "Initial Access"),
        ("Overly permissive IAM role: iam:* on production account",
         "HIGH", "T1078.004", "Valid Accounts"),
        ("Container image with critical CVE deployed to production",
         "HIGH", "T1610", "Deploy Container"),
        ("GCP service account key not rotated in 180+ days",
         "MEDIUM", "T1552.001", "Credentials from Files"),
    ],
    "symantec_dlp": [
        ("GDPR: 2,400 customer records sent to personal Gmail account",
         "CRITICAL", "T1048", "Exfiltration"),
        ("Sensitive financial spreadsheet uploaded to personal Dropbox",
         "HIGH", "T1048.002", "Exfiltration"),
        ("USB data transfer of source code repository detected",
         "HIGH", "T1052.001", "Exfiltration Over Physical Medium"),
        ("PII data included in unencrypted email to external party",
         "MEDIUM", "T1048.003", "Exfiltration Over Alternative Protocol"),
    ],
    "recorded_future": [
        ("Employee credentials found on dark web forum",
         "CRITICAL", "T1589.001", "Gather Victim Identity Information"),
        ("Typosquat domain registered: c0mpany-portal.com",
         "HIGH", "T1583.001", "Acquire Infrastructure"),
        ("Threat actor group 'Lazarus' IOCs match internal traffic",
         "CRITICAL", "T1071", "Command and Control"),
        ("New phishing kit targeting company brand discovered",
         "HIGH", "T1583.001", "Acquire Infrastructure"),
    ],
    "salt_security": [
        ("Shadow API endpoint discovered: /api/v1/internal/users",
         "HIGH", "T1078", "Valid Accounts"),
        ("API credential stuffing attack: 450 failed auth attempts/min",
         "CRITICAL", "T1110.004", "Credential Stuffing"),
        ("Sensitive data in API response: SSN field exposed",
         "HIGH", "T1530", "Data from Cloud Storage"),
        ("Broken object-level authorisation in /api/orders/{id}",
         "HIGH", "T1548", "Abuse Elevation Control Mechanism"),
    ],
    "vectra_ai": [
        ("AI detected anomalous data staging before exfiltration",
         "HIGH", "T1074", "Data Staged"),
        ("Unusual SMB lateral movement pattern across subnet",
         "HIGH", "T1021.002", "Lateral Movement"),
        ("Beaconing detected to newly registered domain",
         "CRITICAL", "T1071.001", "Web Protocols"),
        ("Kerberoasting attack pattern detected",
         "HIGH", "T1558.003", "Kerberoasting"),
    ],
    "cyberark": [
        ("Privileged account accessed from new geolocation",
         "HIGH", "T1078.003", "Local Accounts"),
        ("Service account password unchanged for 365+ days",
         "MEDIUM", "T1078", "Valid Accounts"),
        ("Multiple failed sudo attempts — possible privilege escalation",
         "HIGH", "T1548.003", "Sudo and Sudo Caching"),
        ("Domain Admin logged in outside business hours",
         "HIGH", "T1078.002", "Domain Accounts"),
    ],
}

GENERIC_ALERTS = {
    "zscaler": [
        ("SASE policy violation: access to sanctioned country",
         "HIGH", "T1090", "Proxy"),
        ("Data threshold exceeded on CASB — potential exfil via O365",
         "HIGH", "T1048", "Exfiltration"),
        ("Malware C2 domain blocked by Zscaler ThreatCloud",
         "MEDIUM", "T1071", "C2"),
    ],
    "cloudflare_waf": [
        ("SQL injection attempt blocked on /api/search endpoint",
         "MEDIUM", "T1190", "Exploit Public App"),
        ("DDoS attack mitigated: 1.2M rps volumetric flood",
         "HIGH", "T1498", "Network DoS"),
        ("Bot scraping campaign blocked: 90k requests in 10 min",
         "LOW", "T1595", "Active Scanning"),
    ],
    "extrahop": [
        ("DNS tunnelling detected — possible covert C2 channel",
         "CRITICAL", "T1071.004", "DNS"),
        ("Unusual SMB traffic volume between two workstations",
         "MEDIUM", "T1021.002", "Lateral Movement"),
    ],
    "intune": [
        ("15 devices with non-compliant OS version accessing email",
         "MEDIUM", "T1078", "Valid Accounts"),
        ("Corporate device enrolled in personal Apple ID — data risk",
         "LOW", "T1537", "Transfer Data to Cloud Account"),
    ],
    "knowbe4": [
        ("Phishing simulation click rate this month: 18% (threshold 5%)",
         "HIGH", "T1566", "Phishing"),
        ("3 employees reported real phishing email — validated IOC",
         "MEDIUM", "T1566", "Phishing"),
    ],
}

ALL_SAMPLE_ALERTS = {**SAMPLE_ALERTS, **GENERIC_ALERTS}


def random_hostname():
    prefixes = ["ws", "srv", "dc", "sql", "web", "api", "vpn", "db", "mail"]
    return f"{random.choice(prefixes)}-{random.randint(1000,9999)}"


def random_user():
    first = ["alice", "bob", "carlos", "diana", "ethan", "fatima",
             "george", "hana", "ivan", "julia", "kim", "leon"]
    domains = ["corp.local", "company.com", "internal.org"]
    return f"{random.choice(first)}@{random.choice(domains)}"


def generate_alert(source_tool: str, now: datetime) -> dict:
    alerts = ALL_SAMPLE_ALERTS.get(source_tool)
    if not alerts:
        # Generic fallback
        title = f"Security event detected by {source_tool}"
        severity = random.choices(SEVERITIES, SEVERITY_WEIGHTS)[0]
        mitre = "T1078"
        tactic = "Initial Access"
    else:
        title, severity, mitre, tactic = random.choice(alerts)

    hours_ago = random.expovariate(0.1)
    event_time = now - timedelta(hours=min(hours_ago, 720))

    risk_map = {"CRITICAL": 90, "HIGH": 70, "MEDIUM": 45, "LOW": 20, "INFO": 5}
    base_score = risk_map[severity]
    risk_score = min(100, base_score + random.uniform(-10, 10))

    return {
        "cas_id": str(uuid.uuid4()),
        "source_tool": source_tool,
        "source_id": f"{source_tool.upper()}-{random.randint(10000, 99999)}",
        "ingested_at": event_time.isoformat(),
        "event_time": event_time.isoformat(),
        "severity": severity,
        "category": random.choice(CATEGORIES),
        "title": title,
        "description": f"Automated detection via {source_tool} platform.",
        "affected_assets": [
            random_hostname(),
            random_user() if random.random() > 0.5 else random_hostname()
        ],
        "affected_region": random.choices(REGIONS, REGION_WEIGHTS)[0],
        "affected_cloud": random.choices(CLOUDS, CLOUD_WEIGHTS)[0],
        "mitre_tactic": tactic,
        "mitre_technique": mitre,
        "iocs": {
            "hashes": [uuid.uuid4().hex[:64]] if random.random() > 0.7 else [],
            "ips": [f"185.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"]
                   if random.random() > 0.6 else [],
            "domains": [f"malicious-{uuid.uuid4().hex[:6]}.com"] if random.random() > 0.8 else [],
            "urls": []
        },
        "risk_score": round(risk_score, 2),
        "risk_score_rationale": f"Severity {severity} with asset context",
        "status": random.choices(
            ["NEW", "IN_PROGRESS", "RESOLVED", "SUPPRESSED"],
            [0.4, 0.25, 0.30, 0.05]
        )[0]
    }


def generate_posture_history(days: int = 30) -> list:
    now = datetime.now(timezone.utc)
    snapshots = []
    base_score = 68.0
    for d in range(days, -1, -1):
        t = now - timedelta(days=d)
        # Simulate a security incident around day 20 causing score drop
        if 22 >= d >= 18:
            variation = random.uniform(-8, -2)
        elif 17 >= d >= 14:
            variation = random.uniform(-4, 2)
        else:
            variation = random.uniform(-3, 4)
        base_score = max(40, min(92, base_score + variation))
        snapshots.append({
            "snapshot_time": t.isoformat(),
            "overall_score": round(base_score, 1),
            "endpoint_score": round(base_score + random.uniform(-5, 8), 1),
            "cloud_score": round(base_score + random.uniform(-10, 5), 1),
            "identity_score": round(base_score + random.uniform(-3, 10), 1),
            "email_score": round(base_score + random.uniform(-8, 6), 1),
            "network_score": round(base_score + random.uniform(-6, 7), 1),
            "vulnerability_score": round(base_score - random.uniform(0, 15), 1),
            "critical_count": max(0, int(20 - base_score / 5 + random.randint(-2, 5))),
            "high_count": max(0, int(40 - base_score / 4 + random.randint(-5, 10))),
            "medium_count": max(0, int(80 - base_score / 2 + random.randint(-10, 20))),
            "low_count": max(0, int(150 + random.randint(-20, 30))),
            "active_incidents": max(0, random.randint(1, 8)),
            "mttd_minutes": round(random.uniform(8, 45), 1),
            "mttr_minutes": round(random.uniform(30, 240), 1),
        })
    return snapshots


def generate_region_risk() -> list:
    regions = {
        "AE": {"name": "UAE", "assets": 4200, "lat": 24.47, "lng": 54.37},
        "GB": {"name": "United Kingdom", "assets": 8500, "lat": 51.51, "lng": -0.13},
        "US": {"name": "United States", "assets": 12000, "lat": 37.09, "lng": -95.71},
        "DE": {"name": "Germany", "assets": 5200, "lat": 51.17, "lng": 10.45},
        "SG": {"name": "Singapore", "assets": 3100, "lat": 1.35, "lng": 103.82},
        "ZA": {"name": "South Africa", "assets": 2200, "lat": -30.56, "lng": 22.94},
        "BR": {"name": "Brazil", "assets": 2800, "lat": -14.24, "lng": -51.93},
        "IN": {"name": "India", "assets": 6300, "lat": 20.59, "lng": 78.96},
        "FR": {"name": "France", "assets": 3800, "lat": 46.23, "lng": 2.21},
        "JP": {"name": "Japan", "assets": 2900, "lat": 36.20, "lng": 138.25},
        "AU": {"name": "Australia", "assets": 3200, "lat": -25.27, "lng": 133.78},
        "CA": {"name": "Canada", "assets": 2600, "lat": 56.13, "lng": -106.35},
    }
    results = []
    for code, info in regions.items():
        critical = random.randint(0, 8)
        high = random.randint(2, 20)
        medium = random.randint(10, 60)
        coverage = round(random.uniform(72, 99), 1)
        risk_level = "CRITICAL" if critical > 5 else "HIGH" if critical > 2 or high > 12 else "MEDIUM" if high > 5 else "LOW"
        results.append({
            "region_code": code,
            "region_name": info["name"],
            "total_assets": info["assets"],
            "edr_coverage_pct": coverage,
            "critical_alerts": critical,
            "high_alerts": high,
            "medium_alerts": medium,
            "risk_level": risk_level,
            "lat": info["lat"],
            "lng": info["lng"],
        })
    return results


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    print("Generating demo data...")

    # Generate alerts
    all_alerts = []
    counts = {
        "crowdstrike": 80, "mimecast": 60, "qualys": 70, "wiz": 50,
        "symantec_dlp": 40, "recorded_future": 30, "salt_security": 35,
        "vectra_ai": 40, "cyberark": 30, "zscaler": 35,
        "cloudflare_waf": 45, "extrahop": 25, "intune": 20,
        "knowbe4": 15, "sentinel_siem": 25, "palo_alto": 30,
        "axonius": 10, "prisma_cloud": 30, "darktrace": 20, "veeam": 10,
    }
    for tool, count in counts.items():
        for _ in range(count):
            all_alerts.append(generate_alert(tool, now))

    posture_history = generate_posture_history(30)
    region_risk = generate_region_risk()

    demo_data = {
        "generated_at": now.isoformat(),
        "alert_count": len(all_alerts),
        "alerts": all_alerts,
        "posture_history": posture_history,
        "region_risk": region_risk,
    }

    with open("demo_alerts.json", "w") as f:
        json.dump(demo_data, f, indent=2)

    # Stats
    by_severity = {}
    for a in all_alerts:
        by_severity[a["severity"]] = by_severity.get(a["severity"], 0) + 1

    print(f"Generated {len(all_alerts)} alerts across {len(counts)} tools")
    print(f"Severity distribution: {by_severity}")
    print("Saved to demo_alerts.json")
