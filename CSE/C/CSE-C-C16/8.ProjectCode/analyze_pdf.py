import pypdf

pdf_path = r"d:\Kumar-Projects\Kumar\CSE\C\CSE-C-C16\8.ProjectCode\BASEPAPER_A_Compact_and_Efficient_1_251_Million_Parameter_Machine_Learning_CNN_M_arXiv_2604.11332.pdf"

# Open and read the PDF
with open(pdf_path, 'rb') as file:
    pdf_reader = pypdf.PdfReader(file)
    
    # Extract all text
    full_text = ""
    for page in pdf_reader.pages:
        text = page.extract_text()
        full_text += text + "\n"

# Save to a file for easier analysis
with open("basepaper_full_text.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"Total PDF text extracted: {len(full_text)} characters")
print("Saved to: basepaper_full_text.txt")

# Search for key sections
if "Related Work" in full_text:
    print("\n✓ Found 'Related Work' section")
if "Proposed" in full_text:
    print("✓ Found 'Proposed' section")
if "Existing" in full_text:
    print("✓ Found 'Existing' section")
if "Literature Review" in full_text:
    print("✓ Found 'Literature Review' section")
if "System" in full_text:
    print("✓ Found 'System' mentions")
