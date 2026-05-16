"""
connectors/sap.py — SAP BAPI Connector with Simulation Fallback
================================================================
Mode 1 (Live): SAP_HOST + pyrfc installed → real BAPI calls
Mode 2 (Sim):  No credentials / no pyrfc  → SAP-realistic synthetic data

Simulation mode returns authentic SAP field structures (EKKO, EKPO, RBKP)
so the detection pipeline processes it identically to live data.
"""
import os
import datetime
import random
import logging

logger = logging.getLogger(__name__)


class SAPConnector:
    """
    SAP BAPI connector with graceful simulation fallback.

    Live mode  → uses pyrfc + NetWeaver RFC SDK
    Simulation → returns SAP-realistic synthetic data (same field schema)

    Either way the return format is identical, so detection.py
    doesn't know or care which mode is running.
    """

    # SAP document type codes (real values from SAP table T161)
    _SAP_DOC_TYPES = ["NB", "ZUB", "FO", "MK", "WK", "ZKV"]
    # SAP purchasing organisations (realistic codes)
    _SAP_PORG      = ["1000", "2000", "AAAA", "GB01", "US01", "IN01"]
    # SAP company codes
    _SAP_BUKRS     = ["1000", "2000", "3000", "GB00", "US00"]
    # SAP account assignment categories
    _SAP_KNTTP     = ["K", "A", "F", "P", "U", ""]   # Cost centre, Asset, Order...
    # Real SAP item categories
    _SAP_PSTYP     = ["0", "2", "3", "9"]   # Standard, Consignment, Subcontracting, Limit

    def __init__(self):
        host   = os.environ.get("SAP_HOST")
        sysnr  = os.environ.get("SAP_SYSNR", "00")
        client = os.environ.get("SAP_CLIENT", "100")
        user   = os.environ.get("SAP_USER")
        passwd = os.environ.get("SAP_PASSWORD")

        self._live = False
        self._conn = None

        if all([host, user, passwd]):
            try:
                import pyrfc
                self._conn = pyrfc.Connection(
                    ashost=host, sysnr=sysnr,
                    client=client, user=user, passwd=passwd
                )
                self._live = True
                logger.info("[SAP] Live RFC connection established to %s", host)
            except ImportError:
                logger.warning("[SAP] pyrfc not installed — using simulation mode")
            except Exception as e:
                logger.warning("[SAP] RFC connection failed (%s) — using simulation mode", e)
        else:
            logger.info("[SAP] No SAP_HOST configured — running in simulation mode")

    @property
    def mode(self) -> str:
        return "live" if self._live else "simulation"

    # ── Public API — identical return format regardless of mode ──────────────

    def fetch_purchase_orders(self, date_from: str = None) -> list[dict]:
        """Return PO headers in BAPI_PO_GETITEMS format."""
        if self._live:
            return self._live_fetch_pos(date_from)
        return self._sim_purchase_orders(date_from)

    def fetch_invoices(self, date_from: str = None) -> list[dict]:
        """Return invoice list in BAPI_INCOMINGINVOICE_GETLIST format."""
        if self._live:
            return self._live_fetch_invoices(date_from)
        return self._sim_invoices(date_from)

    def fetch_goods_receipts(self, date_from: str = None) -> list[dict]:
        """Return GR documents — used to detect purchases without matching GR."""
        if self._live:
            return self._live_fetch_gr(date_from)
        return self._sim_goods_receipts(date_from)

    def health_check(self) -> dict:
        if self._live:
            try:
                result = self._conn.call("RFC_PING")
                return {"status": "connected", "mode": "live", "ping": "ok"}
            except Exception as e:
                return {"status": "error", "mode": "live", "error": str(e)}
        return {
            "status": "simulation",
            "mode":   "simulation",
            "note":   "Set SAP_HOST + SAP_USER + SAP_PASSWORD for live RFC connection",
            "bapi_version": "BAPI 3.1 field schema"
        }

    # ── Live RFC methods ─────────────────────────────────────────────────────

    def _live_fetch_pos(self, date_from: str) -> list[dict]:
        result = self._conn.call(
            "BAPI_PO_GETITEMS",
            PURCHASEORDER="",
            ITEMS=[],
            HEADERDATA={"CREAT_DATE": date_from or ""}
        )
        return result.get("POHEADER", [])

    def _live_fetch_invoices(self, date_from: str) -> list[dict]:
        result = self._conn.call(
            "BAPI_INCOMINGINVOICE_GETLIST",
            POSTING_DATE=date_from or ""
        )
        return result.get("INVOICELIST", [])

    def _live_fetch_gr(self, date_from: str) -> list[dict]:
        result = self._conn.call(
            "BAPI_GOODSMVT_GETITEMS",
            MOVEMENT_TYPE="101",
            POSTING_DATE_FROM=date_from or ""
        )
        return result.get("GOODSMVT_ITEM", [])

    # ── Simulation methods — authentic SAP field structures ──────────────────

    def _sim_purchase_orders(self, date_from: str = None) -> list[dict]:
        """
        Returns SAP-realistic PO records using real EKKO/EKPO field names.
        Includes a mix of legitimate POs and ones that would trigger shadow flags.
        """
        today = datetime.date.today()
        records = []
        vendors = [
            "FastParts Ltd", "TechSupplies Co", "GlobalMech", "SafetyFirst",
            "QuickFix Engineering", "PrimeSeal Corp", "NexusProcure",
            "AlliedIndustrial", "RapidResponse GmbH", "ACME Maintenance"
        ]
        depts   = ["Maintenance", "Operations", "Engineering", "Safety", "Facilities"]

        for i in range(15):
            po_date  = today - datetime.timedelta(days=random.randint(0, 30))
            vendor   = random.choice(vendors)
            dept     = random.choice(depts)
            amount   = round(random.uniform(500, 75000), 2)
            doc_type = random.choice(self._SAP_DOC_TYPES)
            # Simulate some POs that are shadow-adjacent (no goods receipt yet)
            has_gr   = random.random() > 0.3

            records.append({
                # EKKO fields (PO Header — real SAP field names)
                "EBELN":  f"45{4500000 + i:07d}",   # PO number
                "BUKRS":  random.choice(self._SAP_BUKRS),
                "BSART":  doc_type,
                "LIFNR":  f"00{1000100 + i:07d}",   # Vendor number
                "EKORG":  random.choice(self._SAP_PORG),
                "BEDAT":  po_date.strftime("%Y%m%d"),
                "WAERS":  "USD",
                "WKURS":  1.0,
                # Enriched for ShadowSync pipeline
                "VENDOR_NAME":   vendor,
                "DEPARTMENT":    dept,
                "NETWR":         amount,            # Net value
                "MWSKZ":         "V1",              # Tax code
                "HAS_GR":        has_gr,            # False = potential shadow
                "KNTTP":         random.choice(self._SAP_KNTTP),
                "PSTYP":         random.choice(self._SAP_PSTYP),
                "_source":       "SAP-SIM",
            })
        return records

    def _sim_invoices(self, date_from: str = None) -> list[dict]:
        """Returns SAP-realistic invoice records using RBKP field names."""
        today   = datetime.date.today()
        records = []
        for i in range(10):
            inv_date = today - datetime.timedelta(days=random.randint(0, 14))
            amount   = round(random.uniform(1200, 95000), 2)
            # Some invoices have no matching PO — these become shadow purchases
            has_po   = random.random() > 0.35

            records.append({
                # RBKP fields (Invoice Header — real SAP field names)
                "BELNR":   f"51{5100000 + i:07d}",  # Document number
                "GJAHR":   str(today.year),
                "BUDAT":   inv_date.strftime("%Y%m%d"),
                "BLDAT":   inv_date.strftime("%Y%m%d"),
                "WRBTR":   amount,                   # Invoice amount
                "WAERS":   "USD",
                "LIFNR":   f"00{1000200 + i:07d}",  # Vendor
                "EBELN":   f"45{4500100 + i:07d}" if has_po else "",  # Ref PO (empty = no PO)
                "ZLSCH":   random.choice(["T", "C", "U", "B"]),       # Payment method
                "ZTERM":   "NT30",
                "HAS_PO":  has_po,
                "_source": "SAP-SIM",
            })
        return records

    def _sim_goods_receipts(self, date_from: str = None) -> list[dict]:
        """Returns SAP-realistic GR records using MSEG field names."""
        today   = datetime.date.today()
        records = []
        for i in range(8):
            gr_date  = today - datetime.timedelta(days=random.randint(0, 21))
            qty      = round(random.uniform(1, 50), 1)
            val      = round(random.uniform(800, 40000), 2)
            has_po   = random.random() > 0.25  # No-PO GR = definite shadow

            records.append({
                # MSEG fields (Material Document — real SAP field names)
                "MBLNR":   f"50{5000000 + i:07d}",
                "MJAHR":   str(today.year),
                "ZEILE":   f"{i + 1:04d}",
                "BWART":   "101",           # GR for PO
                "MATNR":   f"PUMP-{1000 + i:04d}",
                "MENGE":   qty,
                "DMBTR":   val,
                "WAERS":   "USD",
                "EBELN":   f"45{4500050 + i:07d}" if has_po else "",
                "LGORT":   random.choice(["WH-A", "WH-B", "MAIN", "COLD"]),
                "HAS_PO":  has_po,
                "_source": "SAP-SIM",
            })
        return records


# ── Module-level singleton ────────────────────────────────────────────────────
sap_connector = SAPConnector()
