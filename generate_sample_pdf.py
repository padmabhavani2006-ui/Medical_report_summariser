"""
generate_sample_pdf.py
Generates a professional synthetic medical PDF report for testing and demonstration.
Contains fictional laboratory values clearly watermarked as DEMO / SYNTHETIC DATA.
"""

import os
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.lib import colors # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.units import inch # type: ignore
from reportlab.platypus import ( # type: ignore
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # pyright: ignore[reportMissingModuleSource]


def generate_sample_pdf(output_path: str = "sample_medical_report.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F766E')
    )

    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B')
    )

    disclaimer_banner_style = ParagraphStyle(
        'DisclaimerBanner',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#B45309'),
        alignment=1
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E293B')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    cell_highlight = ParagraphStyle(
        'CellHighlight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#DC2626')
    )

    elements = []

    # Banner: DEMO / SYNTHETIC DATA
    banner_data = [[
        Paragraph("⚠️ DEMO / SYNTHETIC DATA - NOT A REAL PATIENT MEDICAL RECORD - FOR EDUCATIONAL USE ONLY", disclaimer_banner_style)
    ]]
    banner_table = Table(banner_data, colWidths=[530])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 14))

    # Header section
    elements.append(Paragraph("APEX HEALTH DIAGNOSTICS & CLINICAL LABORATORY", title_style))
    elements.append(Paragraph("100 Innovation Parkway, Suite 400 | Accreditation ID: LAB-99281-DEMO", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0D9488'), spaceBefore=4, spaceAfter=12))

    # Patient & Specimen Info Table
    patient_info = [
        [
            Paragraph("<b>Patient Name:</b> Jane Synthetic Doe", cell_normal),
            Paragraph("<b>Patient ID:</b> PT-2026-8819", cell_normal),
            Paragraph("<b>Date of Collection:</b> 2026-09-20", cell_normal)
        ],
        [
            Paragraph("<b>Age / Gender:</b> 34 Y / Female", cell_normal),
            Paragraph("<b>Referring Doctor:</b> Dr. Robert Vance, MD", cell_normal),
            Paragraph("<b>Report Date:</b> 2026-09-21", cell_normal)
        ],
        [
            Paragraph("<b>Specimen Type:</b> Whole Blood (EDTA)", cell_normal),
            Paragraph("<b>Department:</b> Hematology", cell_normal),
            Paragraph("<b>Status:</b> Completed / Verified", cell_normal)
        ]
    ]
    info_table = Table(patient_info, colWidths=[180, 180, 170])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # Test Results Header
    elements.append(Paragraph("COMPLETE BLOOD COUNT (CBC) WITH DIFFERENTIAL", section_heading))
    elements.append(Spacer(1, 8))

    # Test Results Table
    results_data = [
        [
            Paragraph("Test Investigation", cell_bold),
            Paragraph("Observed Value", cell_bold),
            Paragraph("Unit", cell_bold),
            Paragraph("Reference Interval", cell_bold),
            Paragraph("Flag / Status", cell_bold)
        ],
        [
            Paragraph("Hemoglobin (Hb)", cell_normal),
            Paragraph("10.8", cell_highlight),
            Paragraph("g/dL", cell_normal),
            Paragraph("12.0 - 16.0", cell_normal),
            Paragraph("LOW", cell_highlight)
        ],
        [
            Paragraph("White Blood Cell Count (WBC)", cell_normal),
            Paragraph("7,200", cell_normal),
            Paragraph("/µL", cell_normal),
            Paragraph("4,000 - 11,000", cell_normal),
            Paragraph("NORMAL", cell_normal)
        ],
        [
            Paragraph("Platelet Count", cell_normal),
            Paragraph("245,000", cell_normal),
            Paragraph("/µL", cell_normal),
            Paragraph("150,000 - 450,000", cell_normal),
            Paragraph("NORMAL", cell_normal)
        ],
        [
            Paragraph("Red Blood Cell (RBC) Count", cell_normal),
            Paragraph("4.1", cell_normal),
            Paragraph("million/µL", cell_normal),
            Paragraph("3.8 - 5.2", cell_normal),
            Paragraph("NORMAL", cell_normal)
        ],
        [
            Paragraph("Hematocrit (PCV)", cell_normal),
            Paragraph("33.5", cell_highlight),
            Paragraph("%", cell_normal),
            Paragraph("36.0 - 46.0", cell_normal),
            Paragraph("LOW", cell_highlight)
        ],
        [
            Paragraph("Mean Corpuscular Volume (MCV)", cell_normal),
            Paragraph("81.7", cell_normal),
            Paragraph("fL", cell_normal),
            Paragraph("80.0 - 100.0", cell_normal),
            Paragraph("NORMAL", cell_normal)
        ],
        [
            Paragraph("Mean Corpuscular Hemoglobin (MCH)", cell_normal),
            Paragraph("26.3", cell_normal),
            Paragraph("pg", cell_normal),
            Paragraph("27.0 - 33.0", cell_normal),
            Paragraph("BORDERLINE LOW", cell_normal)
        ],
        [
            Paragraph("Neutrophils", cell_normal),
            Paragraph("62", cell_normal),
            Paragraph("%", cell_normal),
            Paragraph("40 - 75", cell_normal),
            Paragraph("NORMAL", cell_normal)
        ],
        [
            Paragraph("Lymphocytes", cell_normal),
            Paragraph("29", cell_normal),
            Paragraph("%", cell_normal),
            Paragraph("20 - 45", cell_normal),
            Paragraph("NORMAL", cell_normal)
        ]
    ]

    results_table = Table(results_data, colWidths=[180, 85, 75, 110, 80])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    elements.append(results_table)
    elements.append(Spacer(1, 14))

    # Pathologist Impression
    elements.append(Paragraph("LABORATORY COMMENTS & CLINICAL OBSERVATIONS", section_heading))
    elements.append(Spacer(1, 6))

    impression_text = (
        "<b>Summary:</b> Mild normocytic hypochromic anemia observed with reduced Hemoglobin (10.8 g/dL) "
        "and Hematocrit (33.5%). White blood cell count and platelet parameters are within normal biological limits. "
        "Recommend serum ferritin, iron profile, and clinical evaluation with the primary care physician."
    )
    elements.append(Paragraph(impression_text, cell_normal))
    elements.append(Spacer(1, 14))

    # Verification / Sign-off Footer
    footer_data = [
        [
            Paragraph("<b>Analyzed By:</b> Tech. Samuel Clark, MLT", cell_normal),
            Paragraph("<b>Verified By:</b> Dr. Eleanor Hayes, MD (Pathologist)", cell_normal)
        ]
    ]
    footer_table = Table(footer_data, colWidths=[265, 265])
    footer_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(footer_table)

    # Build Document
    doc.build(elements)
    print(f"Sample PDF generated successfully at: {output_path}")


if __name__ == '__main__':
    generate_sample_pdf()
