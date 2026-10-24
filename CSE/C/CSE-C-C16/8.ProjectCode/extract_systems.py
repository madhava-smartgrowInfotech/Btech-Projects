import re

# Read the full text
with open("basepaper_full_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Find the Related Work section
related_work_match = re.search(r"A\.\s*Related Work(.+?)B\.\s*Research Gap", text, re.DOTALL)
if related_work_match:
    print("=" * 80)
    print("EXISTING/RELATED SYSTEMS")
    print("=" * 80)
    print(related_work_match.group(1)[:3000])
    print("\n[... See full file for complete Related Work section]\n")

# Find the Research Gap section
gap_match = re.search(r"B\.\s*Research Gap and Motivation(.+?)III\.\s*METHODOLOGY", text, re.DOTALL)
if gap_match:
    print("\n" + "=" * 80)
    print("RESEARCH GAP & LIMITATIONS OF EXISTING SYSTEMS")
    print("=" * 80)
    print(gap_match.group(1))

# Find the Proposed Methodology and Architecture
methodology_match = re.search(r"III\.\s*METHODOLOGY(.+?)A\.\s*Dataset", text, re.DOTALL)
if methodology_match:
    print("\n" + "=" * 80)
    print("PROPOSED SYSTEM - METHODOLOGY")
    print("=" * 80)
    print(methodology_match.group(1))

# Find Architecture details
arch_match = re.search(r"C\.\s*Architecture(.+?)D\.", text, re.DOTALL)
if arch_match:
    print("\n" + "=" * 80)
    print("PROPOSED SYSTEM - ARCHITECTURE (PD36-C)")
    print("=" * 80)
    print(arch_match.group(1)[:2500])
    print("\n[... See full file for complete architecture details]\n")

print("=" * 80)
print("SUMMARY: Analysis saved to console")
print("=" * 80)
