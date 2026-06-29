path = r"c:\dev\LG-management\services\api\app\models\ship_repair.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

# Remove foreign_keys from the linked_ncr relationship - SQLAlchemy can infer it
old = 'linked_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys=["linked_ncr_id"])'
new = 'linked_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys="[DailyReport.linked_ncr_id]")'

if old in src:
    src = src.replace(old, new)
    print("Fixed relationship")
else:
    # try other variant
    old2 = "foreign_keys=[\"linked_ncr_id\"]"
    print("Searching for:", repr(old2))
    idx = src.find(old2)
    print("Found at:", idx)
    if idx >= 0:
        print(repr(src[max(0,idx-80):idx+80]))

with open(path, encoding="utf-8", mode="w") as f:
    f.write(src)
print("Done")
