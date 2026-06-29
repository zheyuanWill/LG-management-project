import re

path = r'c:\dev\LG-management\services\api\app\schemas\ship_repair.py'
with open(path, encoding='utf-8') as f:
    src = f.read()

# Replace RepairPlan section (from section header to RepairTask section header)
old_plan = '''# ==================== \u4fee\u8239\u8ba1\u5212 ====================
class RepairPlanBase(BaseModel):
    order_id: int
    source: str
    version: str
    uploaded_by: Optional[int] = None  # \u53ef\u9009\uff0c\u540e\u7aef\u81ea\u52a8\u8bbe\u7f6e
    plan_text: Optional[str] = None
    plan_duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    ai_disassembled: bool = False
    human_confirmed: bool = False


class RepairPlanCreate(BaseModel):
    order_id: int
    source: str
    version: str
    plan_text: Optional[str] = None
    plan_duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator(\'start_date\', \'end_date\', mode=\'before\')
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # \u5982\u679c\u662f\u5b57\u7b26\u4e32\uff0c\u53ea\u53d6\u65e5\u671f\u90e8\u5206
            if \'T\' in v:
                v = v.split(\'T\')[0]
            return date.fromisoformat(v)
        if isinstance(v, datetime):
            return v.date()
        return v


class RepairPlanUpdate(BaseModel):
    source: Optional[str] = None
    version: Optional[str] = None
    plan_text: Optional[str] = None
    plan_duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    ai_disassembled: Optional[bool] = None
    human_confirmed: Optional[bool] = None


class RepairPlanResponse(RepairPlanBase):
    id: int
    uploaded_at: datetime
    ai_disassembled_at: Optional[datetime] = None
    ai_disassembled_by: Optional[int] = None
    human_confirmed_by: Optional[int] = None
    human_confirmed_at: Optional[datetime] = None
    confirm_notes: Optional[str] = None
    ai_task_output: Optional[List[Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True'''

new_plan = '''# ==================== \u4fee\u8239\u8ba1\u5212 ====================
class RepairPlanBase(BaseModel):
    order_id: int
    plan_name: str = "\u4fee\u8239\u8ba1\u5212"
    vessel_name: Optional[str] = None
    uploaded_by: Optional[int] = None
    plan_text: Optional[str] = None
    plan_duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress: int = 0
    status: str = "NOT_STARTED"
    notes: Optional[str] = None
    ai_disassembled: bool = False
    human_confirmed: bool = False
    source: Optional[str] = None
    version: Optional[str] = None


class RepairPlanCreate(BaseModel):
    order_id: int
    plan_name: str
    vessel_name: Optional[str] = None
    plan_text: Optional[str] = None
    plan_duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    version: Optional[str] = None

    @field_validator(\'start_date\', \'end_date\', mode=\'before\')
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            if \'T\' in v:
                v = v.split(\'T\')[0]
            return date.fromisoformat(v)
        if isinstance(v, datetime):
            return v.date()
        return v


class RepairPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    vessel_name: Optional[str] = None
    plan_text: Optional[str] = None
    plan_duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    version: Optional[str] = None
    ai_disassembled: Optional[bool] = None
    human_confirmed: Optional[bool] = None


class RepairPlanResponse(RepairPlanBase):
    id: int
    uploaded_at: datetime
    ai_disassembled_at: Optional[datetime] = None
    ai_task_output: Optional[List[Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True'''

if old_plan in src:
    src = src.replace(old_plan, new_plan)
    print("RepairPlan section updated")
else:
    print("ERROR: RepairPlan old_string not found!")
    # Debug: show what we have
    idx = src.find("class RepairPlanBase")
    if idx >= 0:
        print("Found RepairPlanBase at", idx)
        print(repr(src[idx:idx+100]))

# Replace NCR section
old_ncr = '''# ==================== NCR ====================
class NCRBase(BaseModel):
    ncr_number: str
    order_id: int
    task_id: Optional[int] = None
    anomaly_id: Optional[int] = None
    issue_description: str
    discovered_by: int
    discovered_date: date
    responsible_party: str
    root_cause_analysis: Optional[str] = None
    rectification_requirements: Optional[str] = None
    rectification_responsible_id: Optional[int] = None
    planned_completion_date: Optional[date] = None
    rectification_measures: Optional[str] = None
    review_result: Optional[str] = None
    closed_by: Optional[int] = None
    closed_at: Optional[datetime] = None
    status: str = "PENDING"


class NCRCreate(NCRBase):
    pass


class NCRUpdate(BaseModel):
    issue_description: Optional[str] = None
    discovered_date: Optional[date] = None
    responsible_party: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    rectification_requirements: Optional[str] = None
    rectification_responsible_id: Optional[int] = None
    planned_completion_date: Optional[date] = None
    rectification_measures: Optional[str] = None
    review_result: Optional[str] = None
    status: Optional[str] = None


class NCRResponse(NCRBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True'''

new_ncr = '''# ==================== NCR ====================
class NCRBase(BaseModel):
    ncr_number: str
    order_id: int
    task_id: Optional[int] = None
    anomaly_id: Optional[int] = None
    issue_description: str
    discovered_by: int
    discovered_date: date
    responsible_party: str
    priority: str = "MEDIUM"
    responsible_person: Optional[str] = None
    rectification_deadline: Optional[date] = None
    root_cause_analysis: Optional[str] = None
    rectification_requirements: Optional[str] = None
    rectification_responsible_id: Optional[int] = None
    planned_completion_date: Optional[date] = None
    rectification_measures: Optional[str] = None
    review_result: Optional[str] = None
    closed_by: Optional[int] = None
    closed_at: Optional[datetime] = None
    status: str = "PENDING"


class NCRCreate(NCRBase):
    pass


class NCRUpdate(BaseModel):
    issue_description: Optional[str] = None
    discovered_date: Optional[date] = None
    responsible_party: Optional[str] = None
    priority: Optional[str] = None
    responsible_person: Optional[str] = None
    rectification_deadline: Optional[date] = None
    root_cause_analysis: Optional[str] = None
    rectification_requirements: Optional[str] = None
    rectification_responsible_id: Optional[int] = None
    planned_completion_date: Optional[date] = None
    rectification_measures: Optional[str] = None
    review_result: Optional[str] = None
    status: Optional[str] = None


class NCRResponse(NCRBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True'''

if old_ncr in src:
    src = src.replace(old_ncr, new_ncr)
    print("NCR section updated")
else:
    print("ERROR: NCR old_string not found!")

with open(path, encoding='utf-8', mode='w') as f:
    f.write(src)
print("Done writing schema file")
