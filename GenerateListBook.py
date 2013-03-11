from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus.flowables import DocIf
import datetime
import calendar
import imaplib
import email
from email.header import decode_header
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from sys import stdout

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('Times New Roman', 'Times New Roman.ttf'))
pdfmetrics.registerFont(TTFont('Times New Roman Bold', 'Times New Roman Bold.ttf'))
registerFontFamily('Times New Roman',normal='Times New Roman',bold='Times New Roman Bold',italic='Times New Roman',boldItalic='Times New Roman Bold')


PAGE_HEIGHT=648
PAGE_WIDTH=432 # 6" x 9" Lulu Hardcover
MARGIN=72

LABEL = "ITP"
IMAP_SERVER = 'imap.gmail.com'
IMAP_USERNAME = ''
IMAP_PASSWORD = ''

# create a list of date objects for a month
MONTH = 11
YEAR = 2012
dates = []
for i in range(calendar.monthrange(YEAR, MONTH)[1]):
  date = datetime.date(YEAR, MONTH, i +1)
  dates.append(date)

# Generate single date:
#date = datetime.date(2012, 11, 2)
#dates.append(date)

# The old way, going back x days
#DAYS_BACK = 2
#dates = []
#for i in reversed(range(1, DAYS_BACK)):
#  date = (datetime.date.today() - datetime.timedelta(i))
#  dates.append(date)


#EMAIL STUFF:
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(IMAP_USERNAME, IMAP_PASSWORD)
mail.list()
# Out: list of "folders" aka labels in gmail.
mail.select(LABEL)


styles = getSampleStyleSheet()
pb = PageBreak()

h1 = PS(name = 'Heading1',
       fontName = 'Times New Roman',
       alignment= 1, # center
       fontSize = 14
        )
p = PS(name = 'Paragraph',
      fontName = 'Times New Roman',
      fontSize = 7,
      leading = 7
        )

msgHeader = [
        ('FONT', (1,0), (1,-1), 'Times New Roman'),
        ('FONT', (0,0), (0,-1), 'Times New Roman Bold'),
        ('FONTSIZE', (0,0), (-1, -1), 7),
        ('LEADING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (0,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
      ]

def chapterPage(canvas, doc):
  canvas.saveState()
  canvas.setFont('Times New Roman',7)
  canvas.drawCentredString(PAGE_WIDTH/2.0, 55, "%s" % doc.page)
  canvas.restoreState()

def decodeHeader(h):
  decoded = decode_header(h) # out of RTF to Unicode
  decoded = decoded[0][0].decode("latin1")
  decoded = decoded.encode("utf-8")
  return decoded

def go():
  doc = SimpleDocTemplate("phello.pdf",
                          pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
                          leftMargin=MARGIN,
                          rightMargin=MARGIN,
                          topMargin=MARGIN,
                          bottomMargin=MARGIN) 
  Story = []

  #for each date in dates:
  for date in dates:
    IMAPdate = date.strftime("%d-%b-%Y")
    result, data = mail.uid('search', None, '(SENTON {date} HEADER TO itp-students@lists.nyu.edu)'.format(date=IMAPdate))
    ids = data[0] # data is a list.
    id_list = ids.split() # ids is a space separated string

    # chapter title is the date: 
    Story.append(Spacer(30, 75))
    Story.append(Paragraph(date.strftime("%A, %B %e, %Y"), h1))
    Story.append(Spacer(30,125))

    style = styles["Normal"]
    i = 1.0
    # for each message:
    for thisID in id_list:
      stdout.write("\rFetching emails from " + IMAPdate + ": %d%%" % int(i/len(id_list) * 100))
      stdout.flush()
      i = i + 1
      result, data = mail.uid('fetch', thisID, "(RFC822)")
      raw_email = data[0][1]
      email_message = email.message_from_string(raw_email)
      for part in email_message.walk():
        # each part is a either non-multipart, or another multipart message
        # that contains further parts... Message is organized like a tree
        if part.get_content_type() == 'text/plain':
          body = part.get_payload() # get the plaintext version of the body
          trimAt = body.find("\nOn") # try to find position where reply qoute starts. Usually newline with "On Dec..."
          body = body[:trimAt] #trim there
          trimAt = body.find("\n--") #Find footers from ITP mailinglist
          body = body[:trimAt] #trim there
          body = body.replace("=20\r", "")
          body = body.strip() # trim remaining whitespace
          body = body.replace("\n", "<br />") #replace newlines with <br /> so they're seen on the PDF
      #text = "<b>FROM:\t</b>" + decodeHeader(email_message['From']) + "<br/><b>TO:\t</b>" + decodeHeader(email_message['To']) + "<br /><b>DATE:\t</b>" + decodeHeader(email_message['Date']) + "<br /><b>SUBJECT:\t</b>" + decodeHeader(email_message['Subject']) + "<br />"
      
      wrappedSubject = Paragraph(decodeHeader(email_message['Subject']), p)

      headerTable = [['FROM:', decodeHeader(email_message['From'])],
                     ['TO:', decodeHeader(email_message['To'])],
                     ['DATE:', decodeHeader(email_message['Date'])],
                     ['SUBJECT:', wrappedSubject]
                     ]
      t = Table(headerTable, style=msgHeader, colWidths=[30, 250])
      #Story.append(Paragraph(text, p))
      t.setStyle(msgHeader)
      t.hAlign = 'LEFT'
      Story.append(t)
      Story.append(Spacer(1,0.1*inch))
      Story.append(Paragraph(body, p))
      Story.append(Spacer(1,0.4*inch))
    stdout.write("\n")
    # make sure chapters are on odd pages:
    Story.append(DocIf("doc.page%2 == 1",[PageBreak(),PageBreak()],[PageBreak()]))

  doc.build(Story, onFirstPage=chapterPage, onLaterPages=chapterPage)

go()