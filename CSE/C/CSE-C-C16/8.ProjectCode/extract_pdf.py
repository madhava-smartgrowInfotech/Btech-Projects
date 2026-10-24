import pypdf

pdf_path = r"d:\Kumar-Projects\Kumar\CSE\C\CSE-C-C16\8.ProjectCode\BASEPAPER_A_Compact_and_Efficient_1_251_Million_Parameter_Machine_Learning_CNN_M_arXiv_2604.11332.pdf"

# Open and read the PDF
with open(pdf_path, 'rb') as file:
    pdf_reader = pypdf.PdfReader(file)
    
    # Extract all text
    full_text = ""
    for page_num, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        full_text += f"\n--- PAGE {page_num + 1} ---\n"
        full_text += text

# Print first 8000 characters to get overview
print(full_text[:8000])
print("\n\n[... PDF has", len(full_text), "total characters ...]")
