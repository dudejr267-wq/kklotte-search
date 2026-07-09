import sys

with open("검색기.html", encoding="utf-8") as f:
    content = f.read()

start = content.find("<script>")
end = content.rfind("</script>")
script = content[start+8:end]

lines = script.split("\n")
in_string = None
str_start_line = 0
issues = []

for line_idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("//"):
        continue
    i = 0
    while i < len(line):
        c = line[i]
        if in_string is None:
            if c in ('"', "'"):
                in_string = c
                str_start_line = line_idx + 1
        elif c == in_string:
            if i == 0 or line[i-1] != "\\":
                in_string = None
        i += 1
    if in_string and in_string != "`":
        issues.append(f"Line {line_idx+1}: Unclosed {in_string!r} started at line {str_start_line}: {line[:100]}")
        in_string = None

if issues:
    for issue in issues[:10]:
        print(issue)
else:
    print("No obvious string issues found")

# Also check for double commas or missing commas in PRODUCTS
print("\n=== PRODUCTS array check ===")
prod_start = script.find("const PRODUCTS = [")
prod_end = script.find("];", prod_start)
products_block = script[prod_start:prod_end+2]
prod_lines = products_block.split("\n")

for i, line in enumerate(prod_lines):
    stripped = line.strip()
    # Check for lines that end an object without a comma before a new object starts
    if stripped.startswith("}") and not stripped.startswith("}]") and not stripped.startswith("};"):
        if not stripped.endswith(","):
            print(f"WARNING: Line {i+1} of PRODUCTS: missing trailing comma? -> {stripped[:80]}")
    # Check for double commas
    if ",," in stripped:
        print(f"WARNING: Double comma at PRODUCTS line {i+1}: {stripped[:80]}")
