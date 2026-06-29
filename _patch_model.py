import sys
sys.stdout.reconfigure(encoding="utf-8")

# --- Patch ship_repair MODEL ---
path = r"c:\dev\LG-management\services\api\app\models\ship_repair.py"
with open(path, encoding="utf-8") as f:
    src = f.read()

# 1. DailyReport fields: replace old columns with new ones
old = (
    '    site_status: Mapped[str] = mapped_column(SQLEnum(DailyReportStatus, create_type=False), nullable=False)\n'
    '    completed_tasks: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    unfinished_tasks: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    unfinished_reason: Mapped[Optional[str]] = mapped_column(SQLEnum(UnfinishedReason, create_type=False))\n'
    '    affects_schedule: Mapped[bool] = mapped_column(Boolean, default=False)\n'
    '    estimated_delay_days: Mapped[Optional[int]] = mapped_column(Integer)\n'
    '    affects_quality: Mapped[bool] = mapped_column(Boolean, default=False)\n'
    '    affects_safety: Mapped[bool] = mapped_column(Boolean, default=False)\n'
    '    requires_gm_decision: Mapped[bool] = mapped_column(Boolean, default=False)\n'
    '    gm_decision_items: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    one_line_summary: Mapped[Optional[str]] = mapped_column(String(500))\n'
    '    notes: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    linked_spare_part_risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("spare_part_risks.id"))'
)
new = (
    '    site_status: Mapped[str] = mapped_column(SQLEnum(DailyReportStatus, create_type=False), nullable=False)\n'
    '    today_work: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    tomorrow_plan: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    affects_schedule: Mapped[bool] = mapped_column(Boolean, default=False)\n'
    '    estimated_delay_days: Mapped[Optional[int]] = mapped_column(Integer)\n'
    '    notes: Mapped[Optional[str]] = mapped_column(Text)\n'
    '    linked_ncr_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ncrs.id"))'
)
if old in src:
    src = src.replace(old, new); print("DailyReport fields updated")
else:
    print("ERROR DailyReport fields not found"); print(repr(src[src.find("completed_tasks"):src.find("completed_tasks")+50]))

# 2. DailyReport relationship
old2 = '    linked_spare_part_risk: Mapped[Optional["SparePartRisk"]] = relationship("SparePartRisk", foreign_keys=[linked_spare_part_risk_id])'
new2 = '    linked_ncr: Mapped[Optional["NCR"]] = relationship("NCR", foreign_keys=[linked_ncr_id])'
if old2 in src:
    src = src.replace(old2, new2); print("DailyReport rel updated")
else:
    print("WARN DailyReport rel not found (may already be updated)")

# 3. NCR model: add priority, responsible_person, rectification_deadline
old3 = (
    '    status: Mapped[str] = mapped_column(SQLEnum(NCRStatus, create_type=False), default=NCRStatus.PENDING)\n'
    '    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")'
)
new3 = (
    '    status: Mapped[str] = mapped_column(SQLEnum(NCRStatus, create_type=False), default=NCRStatus.PENDING)\n'
    '    priority: Mapped[str] = mapped_column(SQLEnum(NCRPriority, create_type=False), default=NCRPriority.MEDIUM)\n'
    '    responsible_person: Mapped[Optional[str]] = mapped_column(String(200))\n'
    '    rectification_deadline: Mapped[Optional[date]] = mapped_column(Date)\n'
    '    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")'
)
if old3 in src:
    src = src.replace(old3, new3); print("NCR new fields added")
else:
    print("ERROR NCR status not found")

with open(path, encoding="utf-8", mode="w") as f:
    f.write(src)
print("Model file written OK")
