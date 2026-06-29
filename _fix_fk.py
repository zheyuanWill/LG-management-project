path = r"c:\dev\LG-management\services\api\app\models\ship_repair.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

# Fix the foreign_keys reference - use string form
old = 'foreign_keys=[linked_ncr_id]'
new = 'foreign_keys=["linked_ncr_id"]'

if old in src:
    src = src.replace(old, new)
    print("Fixed foreign_keys reference")
else:
    print("Pattern not found")

with open(path, encoding="utf-8", mode="w") as f:
    f.write(src)
print("File written")
