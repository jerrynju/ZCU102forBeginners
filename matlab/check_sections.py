import re

# Read the current v2 file
with open("D:/Code2026/ZCU102/zcu102_learning_hub_v2.html", "r", encoding="utf-8") as f:
    content = f.read()

print(f"Original length: {len(content)} chars")

# Check what sections exist
import re
sections = re.findall(r'id="([^"]*)"', content)
section_ids = [s for s in sections if s.startswith("sec-")]
print(f"Section IDs found: {section_ids}")

# Check nav items
nav_targets = re.findall(r'data-target="([^"]*)"', content)
print(f"Nav targets: {nav_targets}")
