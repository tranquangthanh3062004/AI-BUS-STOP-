import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("data/hanoi/vinbus_dien_hanoi.txt", "r", encoding="utf-8") as f:
    content = f.read()

blocks = re.split(r"(?=(?:-\s*Mã số:\s*[A-Za-z0-9]+|Tuyến(?: xe buýt)?(?: Hà Nội)?(?: số)?\s*[A-Za-z0-9]+[:\s]))", content, flags=re.IGNORECASE)

for b in blocks:
    if "153" in b:
        print("Block:")
        print(b)
        m_itin = re.search(r"(?:Lộ trình|Lộ trình chính)[^:\n]*:\s*([^\n]+)", b, re.IGNORECASE)
        print("Match:", m_itin.group(1) if m_itin else "NONE")
