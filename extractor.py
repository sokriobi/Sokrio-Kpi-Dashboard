# -*- coding: utf-8 -*-
"""
Sokrio KPI Extractor - Core Module
Authentication + Daily Report API Extraction for BDFP & HBC

Auth flow: GET /sanctum/csrf-cookie -> POST /api/v1/login (email + password + device_name)
Response structure:
  {"dailyReports": {"<metric>": [{"territory_id": 1, "territory_name": "...", "value": 251}]}}
"""
import requests
import json
import pandas as pd
from urllib.parse import unquote
from datetime import datetime, timedelta
from typing import Optional

CLIENTS = [
    {
        "name": "BDFP",
        "org": "BRAC Dairy & Food Project",
        "base_url": "https://bdfp.report.sokrio.com",
        "email": "admin@bdfp.com",
        "password": "bdfp@password"
    },
    {
        "name": "HBC",
        "org": "Heidelberg Cement Bangladesh Limited",
        "base_url": "https://hbc.sokrio.com",
        "email": "super@hbc.com",
        "password": "password"
    },
    {
        "name": "BEOL",
        "org": "BEOL",
        "base_url": "https://beol.report.sokrio.com",
        "email": "super@beol.com",
        "password": "beol@password"
    },
    {
        "name": "BIR group",
        "org": "BIR group",
        "base_url": "https://birgh.report.sokrio.com",
        "email": "admin@birgh.com",
        "password": "birgrouphrd"
    },
    {
        "name": "Tradesworth",
        "org": "Tradesworth",
        "base_url": "https://thl.report.sokrio.com",
        "email": "admin@thl.com",
        "password": "password"
    },
    {
        "name": "Paragon Agro Ltd.",
        "org": "Paragon Agro Ltd.",
        "base_url": "https://paragon.report.sokrio.com",
        "email": "super@paragon.com",
        "password": "PGIT123@@@"
    },
    {
        "name": "Muazuddin Steel Industries Limited",
        "org": "Muazuddin Steel Industries Limited",
        "base_url": "https://msi.report.sokrio.com",
        "email": "super@msi.com",
        "password": "password123"
    },
    {
        "name": "Fair Foods & lifestyle",
        "org": "Fair Foods & lifestyle",
        "base_url": "https://ffl.report.sokrio.com",
        "email": "super@ffl.com",
        "password": "Ffl@salesops"
    },
    {
        "name": "Family Crafts",
        "org": "Family Crafts",
        "base_url": "https://familycrafts.report.sokrio.com",
        "email": "super@familycrafts.com",
        "password": "password123"
    },
    {
        "name": "Winpower Group",
        "org": "Winpower Group",
        "base_url": "https://winpower.report.sokrio.com",
        "email": "super@winpower.com",
        "password": "password123"
    },
    {
        "name": "Amin Square BD Ltd",
        "org": "Amin Square BD Ltd",
        "base_url": "https://asl.report.sokrio.com",
        "email": "super@asl.com",
        "password": "password123"
    },
    {
        "name": "Zinix incorporation",
        "org": "Zinix incorporation",
        "base_url": "https://zinix.report.sokrio.com",
        "email": "super@zinix.com",
        "password": "password123"
    },
    {
        "name": "Trust Infinity Firms Bangladesh (TIFBD)",
        "org": "Trust Infinity Firms Bangladesh (TIFBD)",
        "base_url": "https://saadsavory.report.sokrio.com",
        "email": "super@saadsavory.com",
        "password": "password123"
    },
    {
        "name": "M. M. Ispahani Limited",
        "org": "M. M. Ispahani Limited",
        "base_url": "https://itl.report.sokrio.com",
        "email": "super@itl.com",
        "password": "password123"
    },
    {
        "name": "MMCH Monno Medical College & Hospital",
        "org": "MMCH Monno Medical College & Hospital",
        "base_url": "https://mmch.report.sokrio.com",
        "email": "admin@mmch.com",
        "password": "password"
    },
    {
        "name": "Orient Machineries",
        "org": "Orient Machineries",
        "base_url": "https://omt.report.sokrio.com",
        "email": "admin@omt.com",
        "password": "12345678"
    },
    {
        "name": "Lal Teer- Sokrio Advance",
        "org": "Lal Teer- Sokrio Advance",
        "base_url": "https://lalteer.report.sokrio.com",
        "email": "super@lalteer.com",
        "password": "Ltsok#@1234"
    },
    {
        "name": "Royal Weaving",
        "org": "Royal Weaving",
        "base_url": "https://royalpolycoat.report.sokrio.com",
        "email": "super@royalpolycoat.com",
        "password": "salim.hr@royal"
    },
    {
        "name": "Temakaw Fashion limited",
        "org": "Temakaw Fashion limited",
        "base_url": "https://temakaw.report.sokrio.com",
        "email": "super@temakaw.com",
        "password": "password123"
    },
    {
        "name": "Popy Library",
        "org": "Popy Library",
        "base_url": "https://popy.report.sokrio.com",
        "email": "super@popy.com",
        "password": "password123"
    },
    {
        "name": "Barakah Bites Ltd.",
        "org": "Barakah Bites Ltd.",
        "base_url": "https://bbl.report.sokrio.com",
        "email": "super@bbl.com",
        "password": "password123"
    },
    {
        "name": "S. Hoque International",
        "org": "S. Hoque International",
        "base_url": "https://shoque.report.sokrio.com",
        "email": "super@shoque.com",
        "password": "password123"
    },
    {
        "name": "Bd Star Agro",
        "org": "Bd Star Agro",
        "base_url": "https://bdstar.report.sokrio.com",
        "email": "super@bdstar.com",
        "password": "password123"
    },
    {
        "name": "Cfil Chef food",
        "org": "Cfil Chef food",
        "base_url": "https://cfil.report.sokrio.com",
        "email": "super@cfil.com",
        "password": "password123"
    },
    {
        "name": "Kitty Industries Ltd.",
        "org": "Kitty Industries Ltd.",
        "base_url": "https://kitty.report.sokrio.com",
        "email": "super@kitty.com",
        "password": "password123"
    },
    {
        "name": "Rangpur Dairy RD",
        "org": "Rangpur Dairy RD",
        "base_url": "https://rdfpl.report.sokrio.com",
        "email": "super@rdfpl.com",
        "password": "BlsR|424!"
    },
    {
        "name": "Olympic Milk Food Packaging Industries Pvt. Ltd.",
        "org": "Olympic Milk Food Packaging Industries Pvt. Ltd.",
        "base_url": "https://meadow.report.sokrio.com",
        "email": "super@meadow.com",
        "password": "05064782"
    },
    {
        "name": "Supreme Ifad Consumer Pvt. LTD",
        "org": "Supreme Ifad Consumer Pvt. LTD",
        "base_url": "https://supremeifad.report.sokrio.com",
        "email": "super@supremeifad.com",
        "password": "Qwerty787393"
    },
    {
        "name": "Ahmed food",
        "org": "Ahmed food",
        "base_url": "https://afpl.report.sokrio.com",
        "email": "super@afpl.com",
        "password": "Password123"
    },
    {
        "name": "SINOPEC",
        "org": "SINOPEC",
        "base_url": "https://sinopecbd.report.sokrio.com",
        "email": "super@sinopecbd.com",
        "password": "Password123"
    },
    {
        "name": "Smile Food Production Ltd",
        "org": "Smile Food Production Ltd",
        "base_url": "https://sfpl.report.sokrio.com",
        "email": "super@sfpl.com",
        "password": "Password123"
    },
    {
        "name": "Bengal Group of Industries",
        "org": "Bengal Group of Industries",
        "base_url": "https://romania.report.sokrio.com",
        "email": "super@romania.com",
        "password": "Password123"
    },
    {
        "name": "Manola",
        "org": "Manola",
        "base_url": "https://manola.report.sokrio.com",
        "email": "super@manola.com",
        "password": "Password123"
    },
    {
        "name": "Linkage",
        "org": "Linkage",
        "base_url": "https://linkageiltd.report.sokrio.com",
        "email": "super@linkageiltd.com",
        "password": "Password123"
    },
    {
        "name": "Bengal Polymer Wares Limited",
        "org": "Bengal Polymer Wares Limited",
        "base_url": "https://bpwl.report.sokrio.com",
        "email": "super@bpwl.com",
        "password": "Polymer123"
    },
    {
        "name": "Rahul Group",
        "org": "Rahul Group",
        "base_url": "https://rahulgrp.report.sokrio.com",
        "email": "super@rahulgrp.com",
        "password": "64681990"
    },
    {
        "name": "R B Agro",
        "org": "R B Agro",
        "base_url": "https://rbagro.report.sokrio.com",
        "email": "super@rbagro.com",
        "password": "Rbagro123"
    },
    {
        "name": "Astro Engineering Ltd",
        "org": "Astro Engineering Ltd",
        "base_url": "https://astro.report.sokrio.com",
        "email": "super@astro.com",
        "password": "Astro123"
    },
    {
        "name": "Min Max",
        "org": "Min Max",
        "base_url": "https://minmax.report.sokrio.com",
        "email": "super@minmax.com",
        "password": "Minmax1234"
    },
    {
        "name": "Dhaka Ice Cream Industries Limited",
        "org": "Dhaka Ice Cream Industries Limited",
        "base_url": "https://polarbd.report.sokrio.com",
        "email": "super@polarbd.com",
        "password": "Polarbd2026"
    }
]

KPI_METRICS = [
    {"only": "checkInDsrCount", "is_report": "1", "label": "CheckIn (Report)"},
    {"only": "checkInDsrCount", "is_report": "0", "label": "CheckIn (Non-Report)"},
    {"only": "outletsVisited",  "label": "Outlets Visited"},
    {"only": "orderCreated",    "label": "Order Created"},
    {"only": "orderAmount",     "label": "Order Amount"},
    {"only": "deliveredCreated","label": "Delivered Created"},
    {"only": "deliveredAmount", "label": "Delivered Amount"},
]


class SokrioClient:
    def __init__(self, config: dict):
        self.name = config["name"]
        self.org = config.get("org", config["name"])
        self.base_url = config["base_url"].rstrip("/")
        self.email = config["email"]
        self.password = config["password"]
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_info: Optional[dict] = None
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36",
        })

    def login(self) -> bool:
        """Authenticate using Laravel Sanctum token flow."""
        print(f"  [{self.name}] Getting CSRF cookie...")
        self.session.get(f"{self.base_url}/sanctum/csrf-cookie", timeout=15)
        xsrf = unquote(self.session.cookies.get("XSRF-TOKEN", ""))

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-XSRF-TOKEN": xsrf,
            "Referer": f"{self.base_url}/login",
            "Origin": self.base_url,
        }
        payload = {
            "email": self.email,
            "password": self.password,
            "device_name": "python-kpi-extractor"
        }

        print(f"  [{self.name}] Posting credentials to /api/v1/login ...")
        r = self.session.post(f"{self.base_url}/api/v1/login", json=payload, headers=headers, timeout=15)

        if r.status_code in [200, 201]:
            data = r.json()
            self.token = data.get("token")
            self.user_info = data.get("user", {})
            org_name = self.user_info.get("org", {}).get("name", self.name)
            print(f"  [{self.name}] [OK] Login SUCCESS! Org: {org_name}")
            print(f"  [{self.name}]    Token: {(self.token or '')[:25]}...")
            return True
        else:
            print(f"  [{self.name}] [FAIL] Login FAILED! Status: {r.status_code}")
            try:
                print(f"  [{self.name}]    Error: {r.json()}")
            except Exception:
                print(f"  [{self.name}]    Body: {r.text[:200]}")
            return False

    def _api_headers(self) -> dict:
        return {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Authorization": f"Bearer {self.token}"
        }

    def fetch_kpi(self, only: str, date_from: str, date_to: str, extra_params: dict = None) -> dict:
        """Call /api/v1/daily-reports for a given KPI metric and date range."""
        params = {
            "range": f"{date_from},{date_to}",
            "parent_id": "1",
            "initial": "true",
            "only": only,
        }
        if extra_params:
            params.update(extra_params)

        r = self.session.get(
            f"{self.base_url}/api/v1/daily-reports",
            params=params,
            headers=self._api_headers(),
            timeout=60
        )
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": r.status_code, "message": r.text[:100]}

    def fetch_all_kpis(self, date_from: str, date_to: str) -> dict:
        """Fetch all KPIs and return as a dict keyed by label."""
        results = {}
        for metric in KPI_METRICS:
            label = metric["label"]
            extra = {"is_report": metric["is_report"]} if "is_report" in metric else {}
            data = self.fetch_kpi(metric["only"], date_from, date_to, extra)
            results[label] = data
        return results
