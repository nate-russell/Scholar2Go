from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

pages = convert_from_path('resources/test_docs/1911.10500v2.pdf')
for index, page_pil in enumerate(pages):
    page_pil.save(f'demo_resources/test {index}.jpg', 'JPEG')
