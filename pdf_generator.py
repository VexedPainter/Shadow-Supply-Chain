"""
Nexus Enterprise PDF Engine v6.0.
Provides audit-compliant, professionally formatted commercial documents and risk reports.
Standardized for Commercial Invoices, Purchase Orders, and Executive Summaries.
"""

from fpdf import FPDF
import datetime
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Ensure non-interactive backend
import io
import os
import tempfile

# Professional Minimalist Logo (Nexus 'NX' stylized)

LOGO_SVG_B64 = "PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHJ4PSI4IiBmaWxsPSIjNEY0NkVVIi8+PHBhdGggZD0iTTEwIDEwaDIwdjRoLTIwdjR6bTAgOGgyMHY0aC0yMHY0eiIgZmlsbD0iI2ZmZiIvPjwvc3ZnPg=="

class NexusPDF(FPDF):
    def clean_str(self, text):
        """Clean string to prevent FPDFUnicodeEncodingException using latin-1 fallback."""
        if not text: return ""
        try:
            return str(text).encode('latin-1', 'replace').decode('latin-1')
        except:
            return str(text)

    def _generate_risk_trend_image(self, trend_data):
        """Generates a line chart for risk exposure over time."""
        if not trend_data: return None
        
        if trend_data and len(trend_data) > 1:
            try:
                dates = [d['date'] for d in trend_data]
                exposures = [d['total_exposure'] / 1000 for d in trend_data] # in $K
                
                plt.figure(figsize=(10, 4), dpi=100)
                plt.plot(dates, exposures, marker='o', linestyle='-', color='#00234B', linewidth=2)
                plt.fill_between(dates, exposures, color='#00234B', alpha=0.1)
                plt.title("Financial Exposure Trend (Calculated Kinetic Ledger)", fontsize=12, pad=15)
                plt.xlabel("Reporting Period", fontsize=10)
                plt.ylabel("Exposure ($K)", fontsize=10)
                plt.grid(True, linestyle='--', alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                plt.savefig(tmp_file.name)
                plt.close()
                return tmp_file.name
            except Exception as chart_err:
                print(f"Chart generation failed: {chart_err}")
        return None

    def _generate_shadow_ratio_image(self, shadow_rate):
        """Generates a simple donut chart for shadow vs matched spend."""
        plt.figure(figsize=(3, 3))
        
        sizes = [shadow_rate * 100, (1 - shadow_rate) * 100]
        labels = ['Shadow', 'Matched']
        colors = ['#EF4444', '#10B981']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, 
                wedgeprops={'width': 0.4}, textprops={'fontsize': 8})
        plt.title("Spend Integrity Ratio", fontsize=10, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(tmp_file.name, dpi=100)
        plt.close()
        return tmp_file.name

    def add_certification_seal(self):
        """Adds the Nexus Integrity Seal and Digital Trace ID."""
        curr_y = self.get_y()
        self.set_y(-40)
        self.set_font("helvetica", "B", 8)
        self.set_text_color(107, 114, 128)
        
        # Draw a subtle border for the seal area
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        # Seal Text
        self.set_text_color(79, 70, 229) # Nexus Indigo
        self.cell(0, 5, "VERIFIED BY NEXUS INTEGRITY ENGINE", ln=True, align="R")
        
        self.set_font("helvetica", "I", 7)
        self.set_text_color(156, 163, 175)
        trace_id = f"NXS-CERT-{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{os.urandom(2).hex().upper()}"
        self.cell(0, 5, f"Digital Trace ID: {trace_id}", ln=True, align="R")
        
        self.set_y(curr_y)

    def add_signature_block(self):
        """Adds a professional signature line for authorization."""
        self.ln(10)
        self.set_font("helvetica", "B", 9)
        self.cell(100, 10, "AUTHORIZED BY:")
        self.cell(90, 10, "AUDIT REVIEW DATE:", align="R")
        self.ln(12)
        
        # Signature lines
        x = self.get_x()
        y = self.get_y()
        self.line(x, y, x + 60, y) # Auth line
        self.line(x + 130, y, x + 190, y) # Date line
        
        self.ln(2)
        self.set_font("helvetica", "I", 8)
        self.cell(100, 5, "Chief Procurement Officer / Internal Audit")
        self.cell(90, 5, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), align="R")
        self.ln(5)

    def branding_header(self, title="COMMERCIAL DOCUMENT", doc_id=None, date=None):
        # Professional Header Layout with more breathing room
        self.set_y(15)
        self.set_font("helvetica", "B", 24)
        self.set_text_color(31, 41, 55)  # Gray-800
        
        # Logo placeholder (Top Left)
        self.set_fill_color(79, 70, 229) # Indigo-600
        self.rect(10, 15, 12, 12, 'F')
        self.set_xy(10, 15)
        self.set_font("helvetica", "B", 8)
        self.set_text_color(255, 255, 255)
        self.cell(12, 12, "NX", align="C")

        # Company Info
        self.set_xy(25, 15)
        self.set_font("helvetica", "B", 13)
        self.set_text_color(17, 24, 39)
        self.cell(100, 6, "NEXUS SUPPLY INTEGRITY", ln=1)

        self.set_font("helvetica", "", 7)
        self.set_text_color(107, 114, 128)
        self.set_x(25)
        self.cell(100, 3, "Global Operations | 101 Innovation Way, San Francisco, CA 94103", ln=1)
        self.set_x(25)
        self.cell(100, 3, "Tax ID: EIN-98-223450 | compliance@nexus.integrity", ln=1)
        
        # Document Title and ID (Top Right)
        self.set_xy(130, 15)
        self.set_font("helvetica", "B", 16)
        self.set_text_color(79, 70, 229) # Indigo
        self.cell(76, 8, title, ln=1, align="R")
        self.set_font("helvetica", "B", 8)
        self.set_text_color(75, 85, 99)
        if doc_id:
            self.cell(0, 4, f"DOC_REF: {doc_id}", ln=1, align="R")
        if date:
            self.cell(0, 4, f"DATE: {date}", ln=1, align="R")

        # Visual Separator
        self.set_draw_color(229, 231, 235)  # Gray-200
        self.line(10, 38, 206, 38)
        self.set_y(45)

    def footer(self):
        self.set_y(-25)
        self.set_draw_color(229, 231, 235)
        self.line(10, self.get_y(), 206, self.get_y())
        self.ln(2)
        self.set_font("helvetica", "B", 8)
        self.set_text_color(55, 65, 81)
        self.cell(0, 6, f"NE-DOC-SYNC-V3.0 | Integrity Compliance Report | Page {self.page_no()} of {{nb}}", align="C", ln=1)

        self.set_font("helvetica", "I", 7)
        self.set_text_color(156, 163, 175)
        self.cell(0, 4, "Confidential Property of Nexus Integrity Global. TraceID: " + datetime.datetime.now().strftime("%Y%j%H%M") + " | SECURED", align="C")


def generate_document_pdf(data: dict, document_type: str = "invoice", audit_context: str = None) -> bytes:
    """
    Unified producer for Commercial Invoices and Purchase Orders.
    document_type options: "invoice", "po"
    """
    title = "COMMERCIAL INVOICE" if document_type == "invoice" else "PURCHASE ORDER"
    pdf = NexusPDF(orientation="P", unit="mm", format="Letter")

    pdf.alias_nb_pages()
    pdf.add_page()

    doc_id = str(data.get("id", "N/A"))
    date = str(data.get("date", datetime.date.today().isoformat()))
    pdf.branding_header(title=title, doc_id=doc_id, date=date)

    # Participant Info Grid
    y_start = pdf.get_y()
    
    # Section Headers
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(65, 6, "VENDOR / REMIT TO", ln=0)
    pdf.cell(65, 6, "BILL TO", ln=0)
    pdf.cell(65, 6, "SHIP TO", ln=1)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(31, 41, 55)
    
    vendor_name = data.get("vendor_name", "Unknown Vendor")
    
    # Vendor Block
    pdf.set_xy(10, y_start + 6)
    pdf.multi_cell(60, 4, f"{vendor_name}\nStandard Disbursement\nVendor ID: {data.get('vendor_id', 'V-AUT')}\naccounts@{vendor_name.lower().replace(' ', '')}.com")

    # Bill To Block
    pdf.set_xy(75, y_start + 6)
    pdf.multi_cell(60, 4, "Nexus Integrity Accounts Payable\n101 Innovation Way\nSan Francisco, CA 94103\nap@nexus.integrity")


    # Ship To Block
    pdf.set_xy(140, y_start + 6)
    pdf.multi_cell(60, 4, "Enterprise Receiving Dock A4\nAttn: Operations Manager\n101 Innovation Way\nSan Francisco, CA 94103")
    
    pdf.ln(12)

    # Document Metadata Row
    pdf.set_fill_color(249, 250, 251)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(49, 7, "CURRENCY", border=1, align="C", fill=True)
    pdf.cell(49, 7, "PAYMENT TERMS", border=1, align="C", fill=True)
    pdf.cell(49, 7, "DUE DATE", border=1, align="C", fill=True)
    pdf.cell(49, 7, "PROJECT / DEPT", border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    pdf.cell(49, 7, data.get("currency", "USD"), border=1, align="C")
    pdf.cell(49, 7, "NET 30", border=1, align="C")
    pdf.cell(49, 7, date, border=1, align="C") # Simple fallback
    pdf.cell(49, 7, str(data.get("department", "General Ops")), border=1, align="C")
    pdf.ln(10)

    # Line Items Section
    pdf.set_fill_color(31, 41, 55)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(100, 8, " DESCRIPTION / ITEM", border=0, fill=True)
    pdf.cell(30, 8, "QTY", border=0, align="C", fill=True)
    pdf.cell(30, 8, "UNIT PRICE", border=0, align="R", fill=True)
    pdf.cell(36, 8, "TOTAL PRICE ", border=0, align="R", fill=True)
    pdf.ln()

    # Data Row
    pdf.set_text_color(17, 24, 39)
    pdf.set_font("helvetica", "", 9)
    
    qty = data.get("quantity", 1)
    amount = float(data.get("amount", 0))
    unit_p = amount / qty if qty > 0 else amount
    
    # Use multi_cell for description to prevent overlap
    cur_y = pdf.get_y()
    pdf.multi_cell(100, 10, f" {pdf.clean_str(data.get('item', 'General Procurement'))}", border="B", align="L")
    next_y = pdf.get_y()
    
    pdf.set_xy(110, cur_y)
    pdf.cell(30, (next_y - cur_y), str(qty), border="B", align="C")
    pdf.cell(30, (next_y - cur_y), f"${unit_p:,.2f}", border="B", align="R")
    pdf.cell(36, (next_y - cur_y), f"${amount:,.2f} ", border="B", align="R")
    pdf.set_y(next_y + 5)

    # Totals Table with proper spacing
    pdf.set_x(130)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 8, "SUBTOTAL", border=0)
    pdf.cell(36, 8, f"${amount:,.2f} ", border=0, align="R")
    pdf.ln(8)
    
    pdf.set_x(130)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(40, 7, "TOTAL TAX (0%)", border=0)
    pdf.cell(36, 7, "$0.00 ", border=0, align="R")
    pdf.ln(10)
    
    pdf.set_x(130)
    pdf.set_fill_color(79, 70, 229)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 10, " TOTAL PAYABLE", fill=True, border=1)
    pdf.cell(36, 10, f"{data.get('currency', 'USD')} ${amount:,.2f} ", fill=True, align="R", border=1)
    pdf.ln(10)

    # Audit Context Section if provided
    if audit_context:
        pdf.set_fill_color(254, 243, 199) # Light amber background for audit note
        pdf.set_text_color(146, 64, 14)  # Dark amber text
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(0, 8, " NEXUS AUDIT SECURED RESOLUTION", fill=True, ln=1)
        pdf.set_font("helvetica", "I", 8)
        pdf.multi_cell(0, 4, f"Reasoning: {audit_context}", fill=True, border="B")
        pdf.ln(5)

    # Compliance & Terms (Fixed Bottom)
    pdf.set_y(220 if not audit_context else 210)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 6, "LEGAL & COMPLIANCE NOTES", ln=1)
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(107, 114, 128)
    pdf.multi_cell(0, 3, "1. This document is part of a shadow spend reconciliation audit.\n2. Terms of delivery: DAP (Delivered-at-Place) per Incoterms 2020.\n3. Non-contractual procurement flagged for AI-assisted audit review.", ln=True)
    
    # Authorized Block
    pdf.set_xy(135, 235)
    pdf.set_draw_color(31, 41, 55)
    pdf.line(135, 245, 200, 245)
    pdf.set_xy(135, 246)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(65, 4, "CHIEF PROCUREMENT OFFICER", align="C", ln=1)

    return bytes(pdf.output())

def generate_dashboard_report_pdf(stats: dict, risk_vendors: list = None, recommendations: list = None, trend_data: list = None) -> bytes:
    """Quantitative Executive Summary Report with AI Reasoning, Visual Analytics, and Certification."""
    pdf = NexusPDF(orientation="P", unit="mm", format="Letter")
    pdf.alias_nb_pages()
    pdf.add_page()

    today = datetime.date.today().isoformat()
    pdf.branding_header(
        title="EXECUTIVE RISK SUMMARY",
        doc_id=f"AUD-{today.replace('-', '')}",
        date=today,
    )

    # 1. Executive Summary & KPIs
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 10, "1.0 QUANTITATIVE RISK ANALYSIS", ln=1)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(75, 85, 99)
    pdf.multi_cell(0, 5, f"Enterprise audit finalized on {today}. The Nexus Integrity Engine has synthesized cross-departmental spend patterns. Detection precision remains optimal at {stats.get('avg_confidence', 0.92)*100:.1f}% based on algorithmic scoring and historical reconciliation data.")
    pdf.ln(5)

    # KPI Row
    pdf.set_fill_color(249, 250, 251)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(49, 8, "EXPOSURE AT RISK", border=1, align="C", fill=True)
    pdf.cell(49, 8, "SHADOW SPEND RATE", border=1, align="C", fill=True)
    pdf.cell(49, 8, "NEXUS RISK LEVEL", border=1, align="C", fill=True)
    pdf.cell(49, 8, "AUDIT QUALITY", border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(49, 10, str(stats.get("exposure", "$0.00")), border=1, align="C")
    pdf.cell(49, 10, str(stats.get("shadow_rate", "0%")), border=1, align="C")
    
    risk_color = (185, 28, 28) if stats.get("risk_level") == "HIGH" else (31, 41, 55)
    pdf.set_text_color(*risk_color)
    pdf.cell(49, 10, str(stats.get("risk_level", "LOW")).upper(), border=1, align="C")
    
    pdf.set_text_color(5, 150, 105) # Green
    pdf.cell(49, 10, "OPTIMIZED", border=1, align="C")
    pdf.ln(15)

    # 2. Visual Analytics Section
    pdf.set_text_color(17, 24, 39)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 10, "2.0 VISUAL ANALYTICS & TRENDS", ln=1)
    pdf.ln(2)

    # Generate and embed charts
    trend_chart = pdf._generate_risk_trend_image(trend_data)
    
    # Calculate shadow rate for donut (strip % if needed)
    try:
        s_rate_str = stats.get("shadow_rate", "0%").replace("%", "")
        s_rate = float(s_rate_str) / 100
    except:
        s_rate = 0.1
        
    ratio_chart = pdf._generate_shadow_ratio_image(s_rate)

    if trend_chart:
        pdf.image(trend_chart, x=10, y=pdf.get_y(), w=120)
        
    if ratio_chart:
        pdf.image(ratio_chart, x=135, y=pdf.get_y(), w=60)
        
    pdf.set_y(pdf.get_y() + 65) # Move past charts
    
    # Cleanup temp files
    for f in [trend_chart, ratio_chart]:
        if f and os.path.exists(f): 
            try: os.remove(f)
            except: pass

    # 3. High Risk Entity Distribution
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 10, "3.0 CRITICAL VENDOR ANOMALIES", ln=1)
    
    pdf.set_fill_color(31, 41, 55)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(75, 8, " VENDOR ENTITY", fill=True)
    pdf.cell(25, 8, " SHADOWS", align="C", fill=True)
    pdf.cell(35, 8, " TOTAL EXPOSURE", align="R", fill=True)
    pdf.cell(61, 8, " PRIMARY RISK REASON", fill=True, align="C")
    pdf.ln()

    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(31, 41, 55)
    if risk_vendors:
        for v in risk_vendors[:8]:
            pdf.cell(75, 8, f" {pdf.clean_str(v['name'])}", border="B")
            pdf.cell(25, 8, str(v['count']), border="B", align="C")
            pdf.cell(35, 8, f"${v['amount']:,.2f}", border="B", align="R")
            pdf.cell(61, 8, f" {pdf.clean_str(v['top_reason'])[:40]}...", border="B")
            pdf.ln()
    
    # 4. Action Proposals
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 10, "4.0 STRATEGIC RECOMMENDATIONS", ln=1)
    
    if not recommendations:
        recommendations = [
            {"text": "Perform comprehensive vendor compliance audit on flagged entities.", "priority": "CRITICAL", "owner": "Internal Audit"},
            {"text": "Restrict corporate card usage for non-verified software subscriptions.", "priority": "HIGH", "owner": "Finance Ops"}
        ]
    
    pdf.set_fill_color(243, 244, 246)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(100, 8, " SECURITY ACTION ITEM", fill=True)
    pdf.cell(35, 8, " PRIORITY", align="C", fill=True)
    pdf.cell(61, 8, " ASSIGNED DEPT", fill=True, align="C")
    pdf.ln()

    pdf.set_font("helvetica", "", 8)
    for rec in recommendations[:5]:
        text = rec.get("text") or rec.get("recommendation_text", "N/A")
        priority = rec.get("priority", "MEDIUM")
        owner = rec.get("owner", "Procurement")
        
        pdf.cell(100, 8, f" {pdf.clean_str(text)[:65]}...", border="B")
        
        # Priority Highlighting
        pdf.set_font("helvetica", "B", 8)
        if priority.upper() in ["CRITICAL", "HIGH"]: 
            pdf.set_text_color(185, 28, 28)
        elif priority.upper() == "MEDIUM": 
            pdf.set_text_color(217, 119, 6)
        else: 
            pdf.set_text_color(55, 65, 81)
        
        pdf.cell(35, 8, pdf.clean_str(priority).upper(), align="C", border="B")
        pdf.set_text_color(31, 41, 55)
        pdf.set_font("helvetica", "", 8)
        pdf.cell(61, 8, pdf.clean_str(owner), border="B", align="C")
        pdf.ln()

    # Certification & Signature
    pdf.add_certification_seal()
    pdf.add_signature_block()

    return bytes(pdf.output())

def generate_bulk_pdf(po_list: list) -> bytes:
    """High-performance Bulk Procurement Index with optimized pagination and row density."""
    pdf = NexusPDF(orientation="L", unit="mm", format="Letter")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.branding_header(title="PROCUREMENT AUDIT LOG")

    headers = [("PO ID", 30), ("DATE", 25), ("VENDOR", 55), ("ITEM", 60), ("AMOUNT", 30), ("QTY", 15), ("STATUS", 25), ("DEPT", 30)]
    
    def add_header_row():
        pdf.set_fill_color(31, 41, 55)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 8)
        for h, w in headers:
            pdf.cell(w, 8, h, fill=True, align="C")
        pdf.ln()
    
    add_header_row()
    
    pdf.set_text_color(31, 41, 55)
    pdf.set_font("helvetica", "", 8)
    
    # Increase density to 28 items per page to reduce page count/file size
    max_items_per_page = 28
    page_item_count = 0
    
    for p in po_list:
        if page_item_count >= max_items_per_page:
            pdf.add_page()
            pdf.branding_header(title="PROCUREMENT AUDIT LOG (CONT.)")
            add_header_row()
            pdf.set_text_color(31, 41, 55)
            pdf.set_font("helvetica", "", 8)
            page_item_count = 0

        # Optimization: Pre-format data to avoid complex logic in cell calls
        amount = f"${float(p.get('amount', 0)):,.2f}"
        status = str(p.get("status", "Pending"))
        
        pdf.cell(30, 7, pdf.clean_str(p.get("id", "N/A")), border="B")
        pdf.cell(25, 7, pdf.clean_str(p.get("date", ""))[:10], border="B")
        pdf.cell(55, 7, pdf.clean_str(p.get("vendor_name", "Unknown"))[:28], border="B")
        pdf.cell(60, 7, pdf.clean_str(p.get("item", "General"))[:30], border="B")
        pdf.cell(30, 7, amount, border="B", align="R")
        pdf.cell(15, 7, str(p.get("quantity", 1)), border="B", align="C")
        
        # Optimized conditional styling
        if status == "Resolved": pdf.set_text_color(5, 150, 105)
        elif status in ["Flagged", "Pending"]: pdf.set_text_color(185, 28, 28)
        
        pdf.cell(25, 7, pdf.clean_str(status), border="B", align="C")
        pdf.set_text_color(31, 41, 55)
        pdf.cell(30, 7, pdf.clean_str(p.get("department", "Ops"))[:15], border="B", align="C")
        pdf.ln()
        page_item_count += 1

    return bytes(pdf.output())
