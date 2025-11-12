"""Generate PDF reports from markdown insights and trend images."""
from io import BytesIO
from pathlib import Path
from typing import Union, List
import re  # Import re FIRST
import markdown
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
    trend_images: List[BytesIO],
    output_path: Union[str, Path, BytesIO],
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
    
    # Handle output_path: convert Path to string, but keep BytesIO as-is
    if isinstance(output_path, Path):
        output_path = str(output_path)
    # BytesIO and str paths are passed directly to SimpleDocTemplate
    
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
    
    # What This Means For Your Business
    if 'What This Means For Your Business' in sections:
        story.append(Paragraph('What This Means For Your Business', styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        content = sections['What This Means For Your Business']
        # Split by ### headers
        subsections = re.split(r'###\s+', content)
        
        for subsection in subsections:
            if not subsection.strip():
                continue
            
            lines = subsection.strip().split('\n')
            if len(lines) > 0:
                # First line is the header
                header = lines[0].strip()
                body = '\n'.join(lines[1:]).strip()
                
                if header and body:
                    story.append(Paragraph(f"<b>{header}</b>", styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
                    story.append(Paragraph(body, styles['Normal']))
                    story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.25*inch))
    
    # Trends Analysis with explanations
    if 'Trends Analysis' in sections:
        story.append(Paragraph('Trends Analysis', styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        content = sections['Trends Analysis']
        # Split by ### headers (chart titles)
        chart_sections = re.split(r'###\s+', content)
        
        chart_index = 0
        for section in chart_sections:
            if not section.strip():
                continue
            
            lines = section.strip().split('\n')
            if len(lines) > 0:
                chart_title = lines[0].strip()
                
                # Add chart title
                story.append(Paragraph(f"<b>{chart_title}</b>", styles['Heading3']))
                story.append(Spacer(1, 0.1*inch))
                
                # Add chart description and analysis
                for line in lines[1:]:
                    line = line.strip()
                    if line and not line.startswith('*[See Chart'):
                        story.append(Paragraph(line, styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))
                
                # Add corresponding trend image if available
                if chart_index < len(trend_images):
                    try:
                        img = Image(trend_images[chart_index], width=6*inch, height=3.5*inch)
                        story.append(Spacer(1, 0.1*inch))
                        story.append(img)
                        story.append(Spacer(1, 0.05*inch))
                        story.append(Paragraph(f"<i>Figure {chart_index + 1}: {chart_title}</i>", styles['Italic']))
                        chart_index += 1
                    except:
                        pass
                
                story.append(Spacer(1, 0.3*inch))
    else:
        # Fallback: Add trend images with captions if no Trends Analysis section
        for i, img_data in enumerate(trend_images, 1):
            try:
                img = Image(img_data, width=6*inch, height=4*inch)
                story.append(img)
                caption = f"Figure {i}: Trend Analysis {i}"
                story.append(Paragraph(caption, styles['Italic']))
                story.append(Spacer(1, 0.25*inch))
            except:
                pass
    
    # KPI Table - handle multiple section name variations
    kpi_table_sections = ['Key Performance Indicators', 'KPI Table', 'Table']
    kpi_section = None
    for section_name in kpi_table_sections:
        if section_name in sections:
            kpi_section = section_name
            break
        # Also check if any section starts with these names
        for key in sections.keys():
            if key.startswith(section_name):
                kpi_section = key
                break
    
    if kpi_section and sections[kpi_section]:
        story.append(Paragraph('Key Performance Indicators', styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        
        table_data = parse_markdown_table(sections[kpi_section])
        if table_data:
            # Create Table with better formatting
            t = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.4*inch))
    
    # Actionable Insights - handle multiple section name variations
    insights_sections = ['Actionable Insights', 'Key Insights', 'KPI Insights', 'Insights']
    insights_section = None
    for section_name in insights_sections:
        if section_name in sections:
            insights_section = section_name
            break
    
    if insights_section:
        story.append(Paragraph('Actionable Insights', styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        insights_text = sections[insights_section]
        
        # Split by numbered items (1. 2. 3.)
        import re
        items = re.split(r'\n\s*\d+\.\s+', insights_text)
        for i, item in enumerate(items):
            if item.strip():
                # Format as numbered list with better spacing
                text = item.strip()
                if i > 0:  # Skip first empty item
                    story.append(Paragraph(f"<b>{i}.</b> {text}", styles['Normal']))
                    story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.25*inch))
    
    # Recommendations
    rec_sections = ['Recommendations', 'Recommendation']
    rec_section = None
    for section_name in rec_sections:
        if section_name in sections:
            rec_section = section_name
            break
    
    if rec_section:
        story.append(Paragraph('Recommendations', styles['Heading2']))
        story.append(Spacer(1, 0.15*inch))
        recommendations_text = sections[rec_section]
        
        # Split by numbered items
        import re
        items = re.split(r'\n\s*\d+\.\s+', recommendations_text)
        for i, item in enumerate(items):
            if item.strip():
                text = item.strip()
                if i > 0:
                    story.append(Paragraph(f"<b>{i}.</b> {text}", styles['Normal']))
                    story.append(Spacer(1, 0.15*inch))
        
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
    trend_images: List[BytesIO],
    output_dir: Union[str, Path] = None,
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