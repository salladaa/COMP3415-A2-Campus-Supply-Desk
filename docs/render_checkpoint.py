from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader
root = Path(__file__).resolve().parents[1]
src=(root/'docs/CHECKPOINT-A.txt').read_text()
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyA',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9))
styles.add(ParagraphStyle(name='CellA',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=0))
styles.add(ParagraphStyle(name='HeadA',fontName='Helvetica-Bold',fontSize=17,leading=21,spaceAfter=14,textColor=colors.HexColor('#174b6b')))
styles.add(ParagraphStyle(name='SubA',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceAfter=7,textColor=colors.HexColor('#176b80')))
def norm(s):
 return s.replace('–','-').replace('—','-').replace('→','->').replace('’',"'")
def p(s,style='BodyA'):return Paragraph(escape(norm(s)),styles[style])
def table(rows,widths):
 t=Table([[p(c,'CellA') for c in row] for row in rows],colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#a4bdcb')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d2dce2')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 return t
sections=src.split('2. Five Code Problem Diagnoses')
system=sections[0].splitlines()
diag,testing=sections[1].split('3. Short Initial Testing Strategy')
story=[p('Campus Supply Desk - Checkpoint A','HeadA'),p('COMP 3415 | Software Engineering | Santhosh Allada','SubA'),p(system[0],'SubA'),p(system[1])]
rows=[line.split('\t') for line in system if '\t' in line]
story += [table(rows,[165,351]),Spacer(1,12)]
for line in system[2:]:
 if line.strip() and '\t' not in line:story.append(p(line))
story += [PageBreak(),p('2. Five Code Problem Diagnoses','HeadA')]
for line in diag.splitlines():
 if '\t' not in line or line.startswith('#'):continue
 number,problem,evidence,improvement=line.split('\t')
 story += [p(number+'. '+problem,'SubA'),p('Evidence and consequence: '+evidence),p('Proposed improvement: '+improvement),Spacer(1,5)]
story += [PageBreak(),p('3. Short Initial Testing Strategy','HeadA')]
rows=[line.split('\t') for line in testing.splitlines() if '\t' in line]
story += [table(rows,[105,411]),Spacer(1,18)]
for line in testing.splitlines():
 if line.strip() and '\t' not in line:story.append(p(line))
def footer(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#c6d6e0'));canvas.line(48,43,564,43)
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#52697b'))
 canvas.drawString(48,30,'COMP 3415 | Campus Supply Desk | Checkpoint A')
 canvas.drawRightString(564,30,str(doc.page))
out=root/'output/pdf/COMP3415-Checkpoint-A.pdf'
SimpleDocTemplate(str(out),pagesize=(612,792),leftMargin=48,rightMargin=48,topMargin=40,bottomMargin=54,title='Campus Supply Desk - Checkpoint A',author='Santhosh Allada').build(story,onFirstPage=footer,onLaterPages=footer)
r=PdfReader(out);print('Pages:',len(r.pages))
for i,page in enumerate(r.pages):print(i+1,len(page.extract_text()))
