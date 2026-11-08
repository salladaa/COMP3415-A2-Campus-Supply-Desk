"""Render the assignment report; reportlab is an authoring-only dependency."""
from pathlib import Path
from html import escape
import re
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

root = Path(__file__).resolve().parents[1]
source = root / 'docs/REPORT.md'
out = root / 'output/pdf/COMP3415-A2-Report.pdf'
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport', fontName='Helvetica', fontSize=9.5, leading=13,
                          spaceAfter=7, textColor=colors.HexColor('#233044'), splitLongWords=True))
styles.add(ParagraphStyle(name='TitleReport', fontName='Helvetica-Bold', fontSize=21, leading=25,
                          spaceAfter=16, textColor=colors.HexColor('#153e62')))
styles.add(ParagraphStyle(name='SectionReport', fontName='Helvetica-Bold', fontSize=12, leading=16,
                          spaceBefore=6, spaceAfter=7, textColor=colors.HexColor('#176b80')))
story=[]
for page_index, page in enumerate(source.read_text().split('---PAGE---')):
    if page_index:
        story.append(PageBreak())
    for block in page.strip().split('\n\n'):
        # Adjacent headings are separate paragraphs, as are list-like evidence lines.
        blocks=block.splitlines() if block.startswith('#') else [block]
        for text in blocks:
            style='BodyReport'
            if text.startswith('## '):
                style='SectionReport'; text=text[3:]
            elif text.startswith('# '):
                style='TitleReport'; text=text[2:]
            formatted = escape(text).replace('\n','<br/>')
            formatted = re.sub(r'https://[^ <]+', lambda m: '<link href="' + m.group(0) + '" color="#176b80">' + m.group(0) + '</link>', formatted)
            story.append(Paragraph(formatted,styles[style]))

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#c9d8e4'))
    canvas.line(44,43,568,43)
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(colors.HexColor('#506277'))
    canvas.drawString(44,30,'COMP 3415 | Software Rescue Mission')
    canvas.drawRightString(568,30,f'{doc.page}')
    canvas.restoreState()

SimpleDocTemplate(str(out),pagesize=(612,792),leftMargin=44,rightMargin=44,
                  topMargin=38,bottomMargin=54,title='COMP 3415 Assignment 2 - Software Rescue Mission',
                  author='Santhosh Allada').build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
