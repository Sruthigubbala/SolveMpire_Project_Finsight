import os
import random
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_perfect_pdf(output_path="backend/data/test_perfect.pdf"):
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Setup document geometry
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []
    
    # 1. Styles Setup
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#1A365D")
    )
    meta_style = ParagraphStyle(
        'MetaText', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor("#4A5568")
    )
    cell_style = ParagraphStyle(
        'GridCell', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#2D3748")
    )
    header_style = ParagraphStyle(
        'HeaderCell', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold"
    )

    # 2. Add Headers & Metadata Info
    story.append(Paragraph("ACCOUNT STATEMENT", title_style))
    story.append(Spacer(1, 15))
    
    meta_text = """
    <b>Account Holder:</b> Devi S &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Account No:</b> 1234 5678 9012<br/>
    <b>Branch:</b> Anna Nagar, Chennai &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>IFSC Code:</b> SBIN0001234<br/>
    <b>Opening Balance:</b> Rs. 15,420.00 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Statement Period:</b> May 2025
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("TRANSACTION DETAILS — MAY 2025", ParagraphStyle('Sub', parent=title_style, fontSize=12, leading=14)))
    story.append(Spacer(1, 10))

    # 3. Transaction Pool Matrix Generator
    vendor_pool = [
        ("Zomato Food Order", "Food", 320.00, 1250.00, True),
        ("Swiggy Food Delivery", "Food", 150.00, 890.00, True),
        ("Uber Cab Service", "Transport", 250.00, 750.00, True),
        ("Ola Rides", "Transport", 120.00, 450.00, True),
        ("Amazon Shopping", "Shopping", 450.00, 4500.00, True),
        ("Flipkart Online", "Shopping", 300.00, 2500.00, True),
        ("Airtel Mobile Recharge", "Utilities", 399.00, 719.00, True),
        ("Jio Fiber Broadband", "Utilities", 599.00, 999.00, True),
        ("Netflix Subscription", "Subscriptions", 649.00, 649.00, True),
        ("Spotify Premium", "Subscriptions", 119.00, 119.00, True),
        ("Apollo Pharmacy", "Medical", 120.00, 1850.00, True),
        ("Petrol — Indian Oil", "Transport", 1000.00, 2000.00, True),
        ("Groww SIP Investment", "Savings", 2000.00, 5000.00, True),
        ("Udemy Course Fee", "Education", 449.00, 699.00, True)
    ]

    # Baseline calculations
    current_balance = 15420.00
    start_date = datetime(2025, 5, 1)
    
    # Initialize table grid data structure with Headers
    table_data = [[
        Paragraph("Date", header_style),
        Paragraph("Description", header_style),
        Paragraph("Category", header_style),
        Paragraph("Debit (Rs.)", header_style),
        Paragraph("Credit (Rs.)", header_style),
        Paragraph("Balance (Rs.)", header_style)
    ]]

    # Step-by-step assembly of exactly 50 structural lines
    for i in range(1, 51):
        # Scale dates naturally across the month structure
        day_offset = min(30, (i - 1) // 1.6)
        tx_date = (start_date + timedelta(days=day_offset)).strftime("%d-%b-%y")
        
        if i == 1:
            desc, cat, debit, credit, is_debit = "Opening Balance", "Balance", "-", "-", False
        elif i == 2:
            desc, cat, debit, credit, is_debit = "Salary Credit — TCS Ltd", "Income", "-", "45,000.00", False
            current_balance += 45000.00
        elif i == 5:
            desc, cat, debit, credit, is_debit = "House Rent Transfer", "Rent", "12,000.00", "-", True
            current_balance -= 12000.00
        else:
            # Pick a transactional schema randomly from our clean vendor matrix
            pool_item = random.choice(vendor_pool)
            desc = f"{pool_item[0]} #{random.randint(100,999)}"
            cat = pool_item[1]
            val = round(random.uniform(pool_item[2], pool_item[3]), 2)
            is_debit = pool_item[4]
            
            if is_debit:
                debit = f"{val:,.2f}"
                credit = "-"
                current_balance -= val
            else:
                debit = "-"
                credit = f"{val:,.2f}"
                current_balance += val

        # Append formatted cell objects straight into Table tree matrix
        table_data.append([
            Paragraph(tx_date, cell_style),
            Paragraph(desc, cell_style),
            Paragraph(cat, cell_style),
            Paragraph(debit, cell_style),
            Paragraph(credit, cell_style),
            Paragraph(f"{current_balance:,.2f}", cell_style)
        ])

    # 4. Create Document Grid Framework
    # Explicit absolute mapping width distribution spanning full horizontal text line width (540 total)
    col_widths = [65, 155, 75, 75, 75, 96]
    
    tx_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Modern accounting UI block format styling
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    
    story.append(tx_table)
    
    # Build document
    doc.build(story)
    print(f"Success! Perfect PDF created with exactly 50 transactions at: {output_path}")

if __name__ == "__main__":
    generate_perfect_pdf()