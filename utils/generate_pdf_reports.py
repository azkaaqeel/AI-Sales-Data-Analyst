"""Generate PDF reports from markdown insights and trend images."""
from io import BytesIO
from pathlib import Path
import markdown
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def extract_sections(markdown_text):
    """Extract sections from markdown using headings."""
    sections = {}
    current_section = None
    current_content = []
    
    for line in markdown_text.split('\n'):
        if line.startswith('#'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = line.lstrip('#').strip()
        else:
            if current_section:
                current_content.append(line)
            
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
        
    return sections

def parse_markdown_table(table_text):
    """Parse markdown table into list of lists."""
    rows = []
    for line in table_text.strip().split('\n'):
        if '|' not in line:
            continue
        if line.strip().startswith('|---'):
            continue
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        rows.append(cells)
    return rows

def create_pdf_report(
    markdown_text: str,
    trend_images: list[BytesIO],
    output_path: str | Path,
    title: str = "Business Performance Report",
    page_size=A4,
    styles_config: dict = None,
    image_config: dict = None,
    layout_config: dict = None,
):
    """
    Generate a PDF report from markdown insights and trend images with customizable styling.
    
    Args:
        markdown_text: The markdown formatted insights text
        trend_images: List of BytesIO objects containing trend images (PNG format)
        output_path: Where to save the PDF
        title: Report title
        page_size: PDF page size (default A4)
        styles_config: Dict with style customization:
            {
                'title_color': '#2C3E50',  # Hex color for title
                'header_color': '#2C3E50',  # Hex color for section headers
                'table_header_color': '#2C3E50',  # Table header background
                'table_header_text_color': '#FFFFFF',  # Table header text
                'body_font': 'Helvetica',  # Main text font
                'title_font': 'Helvetica-Bold',  # Title font
                'header_font': 'Helvetica-Bold',  # Section header font
                'title_size': 24,  # Title font size
                'header_size': 18,  # Section header font size
                'body_size': 11,  # Main text font size
                'table_size': 10,  # Table text size
            }
        image_config: Dict with image customization:
            {
                'width': 6,  # Width in inches
                'height': 4,  # Height in inches
                'caption_size': 10,  # Caption font size
                'spacing': 0.25,  # Space after image in inches
            }
        layout_config: Dict with layout customization:
            {
                'margins': 72,  # Page margins in points (1 inch = 72 points)
                'spacing': 0.25,  # Default spacing in inches
                'section_spacing': 0.5,  # Space between sections in inches
                'table_style': 'modern',  # 'modern' or 'minimal'
            }
    """
    # Default configurations
    default_styles = {
        'title_color': '#2C3E50',
        'header_color': '#2C3E50',
        'table_header_color': '#2C3E50',
        'table_header_text_color': '#FFFFFF',
        'body_font': 'Helvetica',
        'title_font': 'Helvetica-Bold',
        'header_font': 'Helvetica-Bold',
        'title_size': 24,
        'header_size': 18,
        'body_size': 11,
        'table_size': 10,
    }
    
    default_image = {
        'width': 6,
        'height': 4,
        'caption_size': 10,
        'spacing': 0.25,
    }
    
    default_layout = {
        'margins': 72,
        'spacing': 0.25,
        'section_spacing': 0.5,
        'table_style': 'modern',
    }
    
    # Merge with provided configs, using defaults for missing values
    styles_config = {**default_styles, **(styles_config or {})}
    image_config = {**default_image, **(image_config or {})}
    layout_config = {**default_layout, **(layout_config or {})}
    # Convert Path to string if needed
    output_path = str(output_path)
    
    # Extract sections from markdown
    sections = extract_sections(markdown_text)
    
    # Setup document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Add custom style for headers
    styles.add(
        ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2C3E50'),
        )
    )
    
    story = []
    
    # Title
    story.append(Paragraph(title, styles['CustomHeading1']))
    story.append(Spacer(1, 0.25*inch))
    
    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on {date_str}", styles['Italic']))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary
    if 'Executive Summary' in sections:
        story.append(Paragraph('Executive Summary', styles['Heading2']))
        story.append(Paragraph(sections['Executive Summary'], styles['Normal']))
        story.append(Spacer(1, 0.25*inch))
    
    # Add trend images with captions
    for i, img_data in enumerate(trend_images, 1):
        img = Image(img_data, width=6*inch, height=4*inch)
        story.append(img)
        caption = f"Figure {i}: {'Sales Trend' if i == 1 else 'Components Analysis'}"
        story.append(Paragraph(caption, styles['Italic']))
        story.append(Spacer(1, 0.25*inch))
    
    # KPI Table
    if any(k.startswith('Table') for k in sections.keys()):
        table_section = next(s for s in sections.keys() if s.startswith('Table'))
        if sections[table_section]:
            table_data = parse_markdown_table(sections[table_section])
            if table_data:
                # Create Table
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.25*inch))
    
    # KPI Insights
    if 'KPI Insights' in sections:
        story.append(Paragraph('KPI Insights', styles['Heading2']))
        insights_text = sections['KPI Insights']
        # Split into paragraphs and format
        for paragraph in insights_text.split('\n\n'):
            story.append(Paragraph(paragraph, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    
    # Recommendations
    if 'Recommendations' in sections:
        story.append(Paragraph('Recommendations', styles['Heading2']))
        recommendations_text = sections['Recommendations']
        # Handle bullet points
        for line in recommendations_text.split('\n'):
            if line.strip().startswith('-'):
                text = line.strip()[1:].strip()
                story.append(Paragraph(f"• {text}", styles['Normal']))
            else:
                story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 0.25*inch))
    
    # Next Investigations (if present)
    if 'Next investigations' in sections:
        story.append(Paragraph('Next Steps', styles['Heading2']))
        next_steps = sections['Next investigations']
        for line in next_steps.split('\n'):
            if line.strip().startswith('-'):
                text = line.strip()[1:].strip()
                story.append(Paragraph(f"• {text}", styles['Normal']))
            else:
                story.append(Paragraph(line, styles['Normal']))
    
    # Build PDF
    doc.build(story)

def generate_pdf_from_insights(
    insights_result: str,
    trend_images: list[BytesIO],
    output_dir: str | Path = None,
    filename: str = None,
    title: str = "Business Performance Analysis",
    page_size=A4,
    styles_config: dict = None,
    image_config: dict = None,
    layout_config: dict = None
) -> Path:
    """
    Generate a PDF report from the insights generation result with customizable styling.
    
    Args:
        insights_result: The markdown text from generate_insights()
        trend_images: The list of BytesIO trend images used in insights generation
        output_dir: Optional directory to save the PDF (default: current dir)
        filename: Optional filename (default: business_insights_YYYY_MM_DD.pdf)
        title: Report title (default: "Business Performance Analysis")
        page_size: PDF page size (default: A4)
        styles_config: Dict with style customization (see create_pdf_report docstring)
        image_config: Dict with image customization (see create_pdf_report docstring)
        layout_config: Dict with layout customization (see create_pdf_report docstring)
    
    Returns:
        Path to the generated PDF file
    """
    # Handle output location
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
    # Generate filename if not provided
    if filename is None:
        date_str = datetime.now().strftime("%Y_%m_%d")
        filename = f"business_insights_{date_str}.pdf"
    
    output_path = output_dir / filename
    
    # Generate the PDF
    create_pdf_report(
        markdown_text=insights_result,
        trend_images=trend_images,
        output_path=output_path,
        title="Business Performance Analysis"
    )
    
    return output_path