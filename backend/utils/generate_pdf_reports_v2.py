"""
Generate professional, text-based PDF reports.
Adaptive to any dataset with proper markdown parsing.
"""
import re
from io import BytesIO
from typing import Union, Dict, List
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)


def clean_markdown(text: str) -> str:
    """Convert markdown to HTML for ReportLab."""
    if not text:
        return ""
    
    # Bold: **text** → <b>text</b>
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)
    
    # Italic: *text* → <i>text</i>
    text = re.sub(r'\*([^\*]+)\*', r'<i>\1</i>', text)
    
    # Remove markdown headers (###, ##, #)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Convert line breaks
    text = text.replace('\n', '<br/>')
    
    return text


def parse_kpi_table(markdown_text: str) -> List[List[str]]:
    """Extract KPI table from markdown."""
    lines = markdown_text.split('\n')
    table_data = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('|---'):
            continue
        
        if '|' in line:
            in_table = True
            # Extract cells
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells and not all(c == '' for c in cells):
                table_data.append(cells)
    
    return table_data if len(table_data) > 1 else None


def parse_numbered_list(text: str) -> List[str]:
    """Extract numbered list items."""
    items = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Match: 1. text or - text or • text
        match = re.match(r'^[\d]+\.\s+(.+)$', line)
        if match:
            items.append(match.group(1))
        elif line.startswith('- ') or line.startswith('• '):
            items.append(line[2:])
        elif line and not line.startswith('#'):
            items.append(line)
    
    return items


def create_text_pdf_report(
    report_data: Dict,
    output_path: Union[str, BytesIO],
    title: str = "Sales Analysis Report"
):
    """
    Generate a professional, text-based PDF report.
    
    Args:
        report_data: {
            'summary': str,
            'kpis': [{'name': str, 'value': str, 'description': str}],
            'kpiExplanations': [{'title': str, 'description': str}],
            'trends': [{'title': str, 'insights': {...}}],
            'insights': [str],
            'recommendations': [str]
        }
        output_path: Where to save PDF
        title: Report title
    """
    # Setup document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#3B82F6'),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#6366F1'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=6
    )
    
    # Build story
    story = []
    
    # Title
    story.append(Paragraph(title, title_style))
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on {date_str}", styles['Italic']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    if report_data.get('summary'):
        story.append(Paragraph('Executive Summary', heading_style))
        summary_text = clean_markdown(report_data['summary'])
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Key Performance Indicators Table
    if report_data.get('kpis'):
        story.append(Paragraph('Key Performance Indicators', heading_style))
        
        # Create table data
        table_data = [['Metric', 'Value', 'Period Comparison']]
        for kpi in report_data['kpis']:
            table_data.append([
                kpi.get('name', ''),
                kpi.get('value', ''),
                clean_markdown(kpi.get('description', ''))
            ])
        
        # Create table
        col_widths = [2.5*inch, 1.5*inch, 2.5*inch]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
    
    # What This Means For Your Business
    if report_data.get('kpiExplanations'):
        story.append(Paragraph('What This Means For Your Business', heading_style))
        story.append(Paragraph(
            'Understanding your metrics and how to interpret them:',
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        for explanation in report_data['kpiExplanations']:
            story.append(Paragraph(
                f"<b>{explanation.get('icon', '')} {explanation.get('title', '')}</b>",
                subheading_style
            ))
            desc = clean_markdown(explanation.get('description', ''))
            story.append(Paragraph(desc, body_style))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Category Breakdowns (Safe - won't crash if missing)
    if report_data.get('categoricalBreakdowns'):
        story.append(Paragraph('Category Breakdowns', heading_style))
        story.append(Paragraph(
            'Top performing categories and products:',
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        for breakdown in report_data['categoricalBreakdowns']:
            # Breakdown title
            story.append(Paragraph(
                f"<b>{breakdown.get('title', 'Category')}</b>",
                subheading_style
            ))
            
            # Create table for items
            if breakdown.get('items'):
                table_data = [['Rank', 'Name', 'Value']]
                for idx, item in enumerate(breakdown['items'], 1):
                    table_data.append([
                        str(idx),
                        item.get('name', ''),
                        item.get('value', '')
                    ])
                
                # Create table
                col_widths = [0.6*inch, 3.5*inch, 1.5*inch]
                t = Table(table_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9333EA')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    
                    # Data rows
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Rank centered
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Name left
                    ('ALIGN', (2, 1), (2, -1), 'RIGHT'),   # Value right
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAF5FF')]),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ]))
                story.append(t)
                
                # Show total if truncated
                if breakdown.get('total_categories', 0) > len(breakdown['items']):
                    remaining = breakdown['total_categories'] - len(breakdown['items'])
                    story.append(Paragraph(
                        f"<i>+{remaining} more categories not shown</i>",
                        styles['Italic']
                    ))
                
                story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Trend Analysis (Text-based)
    if report_data.get('trends'):
        story.append(Paragraph('Trend Analysis', heading_style))
        story.append(Paragraph(
            'Detailed analysis of how your metrics have changed over time:',
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, trend in enumerate(report_data['trends'], 1):
            # Trend title
            story.append(Paragraph(
                f"{idx}. {trend.get('title', 'Trend')}",
                subheading_style
            ))
            
            # Trend description
            if trend.get('description'):
                story.append(Paragraph(
                    clean_markdown(trend['description']),
                    body_style
                ))
            
            # Trend insights (text summary)
            if trend.get('insights'):
                insights = trend['insights']
                insight_text = f"""
                <b>Key Observations:</b><br/>
                • Overall Trend: {insights.get('trend', 'N/A').capitalize()} ({insights.get('change', 'N/A')})<br/>
                • Volatility: {insights.get('volatility', 'N/A').capitalize()}<br/>
                • Peak Value: {insights.get('peak', 'N/A')}<br/>
                • Lowest Value: {insights.get('low', 'N/A')}<br/>
                • Average: {insights.get('average', 'N/A')}
                """
                
                if insights.get('anomalies_count', 0) > 0:
                    insight_text += f"<br/>• Anomalies Detected: {insights['anomalies_count']} unusual data points"
                
                story.append(Paragraph(insight_text, bullet_style))
            
            story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Actionable Insights
    if report_data.get('insights'):
        story.append(Paragraph('Actionable Insights', heading_style))
        story.append(Paragraph(
            'Key findings from your data analysis:',
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, insight in enumerate(report_data['insights'], 1):
            cleaned = clean_markdown(insight)
            story.append(Paragraph(f"{idx}. {cleaned}", bullet_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    if report_data.get('recommendations'):
        story.append(Paragraph('Recommendations', heading_style))
        story.append(Paragraph(
            'Suggested actions based on your data:',
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, rec in enumerate(report_data['recommendations'], 1):
            cleaned = clean_markdown(rec)
            story.append(Paragraph(f"{idx}. {cleaned}", bullet_style))
    
    # Build PDF
    doc.build(story)


if __name__ == '__main__':
    # Test with sample data
    test_data = {
        'summary': 'This is a **test** report with *italic* text.',
        'kpis': [
            {'name': 'Revenue', 'value': '$10,000', 'description': '↑ +15% vs last month'},
            {'name': 'Orders', 'value': '250', 'description': '↓ -5% vs last month'},
        ],
        'insights': ['Revenue increased significantly', 'Orders declined slightly'],
        'recommendations': ['Focus on customer retention', 'Improve marketing']
    }
    
    with open('/tmp/test_report.pdf', 'wb') as f:
        create_text_pdf_report(test_data, f)
    print("Test PDF created at /tmp/test_report.pdf")

