import PyPDF2

pdf_path = 'C:\\Users\\licun\\Downloads\\AI risks.pdf'
pdf_path = 'C:\\Users\\licun\\Downloads\\interpreatable and pedagogical examples.pdf'

pdfFileObj = open(pdf_path, 'rb')  # 'rb' for read binary mode
pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
npages = pdfReader.numPages

for n in range(npages):
    print('\nStart of Page Number %d -------------------------\n' % n)

    pageObj = pdfReader.getPage(n)
    text = pageObj.extractText()
    print(repr(text))
