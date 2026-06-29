path = r"c:\dev\LG-management\services\api\app\models\ship_repair.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

# Fix 1: Anomaly should have linked_spare_part_risk, NOT linked_ncr
old1 = (
    '    converted_to_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys=[converted_to_ncr_id])\n'
    '    linked_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys="[DailyReport.linked_ncr_id]")'
)
new1 = (
    '    converted_to_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys=[converted_to_ncr_id])\n'
    '    linked_spare_part_risk: Mapped[Optional["SparePartRisk"]] = relationship("SparePartRisk", foreign_keys=[linked_spare_part_risk_id])'
)
if old1 in src:
    src = src.replace(old1, new1)
    print("Anomaly rel restored OK")
else:
    print("ERROR: Anomaly old rel not found")
    idx = src.find("converted_to_ncr: Mapped")
    print(repr(src[idx:idx+200]))

# Fix 2: DailyReport should have linked_ncr relationship
# Find DailyReport relationships block
# It ends after the reporter relationship
old2 = (
    '    # Relationships\n'
    '    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])\n'
    '    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])\n'
    '    linked_spare_part_risk: Mapped[Optional["SparePartRisk"]] = relationship("SparePartRisk", foreign_keys=[linked_spare_part_risk_id])\n'
    '\n'
    '\nclass PhotoEvidence'
)
new2 = (
    '    # Relationships\n'
    '    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])\n'
    '    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])\n'
    '    linked_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys=[linked_ncr_id])\n'
    '\n'
    '\nclass PhotoEvidence'
)
if old2 in src:
    src = src.replace(old2, new2)
    print("DailyReport linked_ncr rel added OK")
else:
    print("Searching for DailyReport reporter rel...")
    idx = src.find('reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])')
    if idx >= 0:
        print(repr(src[idx:idx+300]))
    else:
        print("Not found either")

with open(path, encoding="utf-8", mode="w") as f:
    f.write(src)
print("Model file written")
