"""
Database Seed Script
"""
import asyncio
from decimal import Decimal
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.customer import Customer, Vessel
from app.models.product import Product, Supplier, SupplierQuote, SupplierType
from app.models.order import Order, OrderLineItem, Quote, QuoteLineItem, ProjectType, OrderStatus, QuoteStatus, Currency
from app.models.contract import Contract, PaymentPlan, ContractStatus
from app.models.tracking import NodeTemplate
from app.models.settlement import CostCategory, ExchangeRate


async def seed_database():
    """Seed database with initial data"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Check if data exists
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping...")
            return
        
        print("Seeding database...")
        
        # ==================== Users ====================
        users = [
            User(
                username="owner",
                email="owner@lg.com",
                hashed_password=get_password_hash("123456"),
                real_name="张老板",
                role=UserRole.OWNER,
                is_active=True
            ),
            User(
                username="pm",
                email="pm@lg.com",
                hashed_password=get_password_hash("123456"),
                real_name="李项目",
                role=UserRole.PM,
                is_active=True
            ),
            User(
                username="proc",
                email="proc@lg.com",
                hashed_password=get_password_hash("123456"),
                real_name="王采购",
                role=UserRole.PROC,
                is_active=True
            ),
            User(
                username="fin",
                email="fin@lg.com",
                hashed_password=get_password_hash("123456"),
                real_name="赵财务",
                role=UserRole.FIN,
                is_active=True
            ),
            User(
                username="ops",
                email="ops@lg.com",
                hashed_password=get_password_hash("123456"),
                real_name="钱仓库",
                role=UserRole.OPS,
                is_active=True
            ),
        ]
        for user in users:
            db.add(user)
        await db.flush()
        
        pm_user = users[1]  # PM user
        
        # ==================== Customers ====================
        customers = [
            Customer(
                name="中远海运集团",
                code="COSCO",
                contact_person="陈经理",
                contact_phone="13800138001",
                contact_email="chen@cosco.com",
                address="上海市浦东新区东方路xxx号"
            ),
            Customer(
                name="招商轮船",
                code="CMB",
                contact_person="林经理",
                contact_phone="13800138002",
                contact_email="lin@cmb.com",
                address="深圳市南山区蛇口港xxx号"
            ),
            Customer(
                name="长荣海运",
                code="EVERGREEN",
                contact_person="吴经理",
                contact_phone="13800138003",
                contact_email="wu@evergreen.com",
                address="台湾高雄市xxx路xxx号"
            ),
        ]
        for customer in customers:
            db.add(customer)
        await db.flush()
        
        # ==================== Vessels ====================
        vessels = [
            Vessel(
                name="远洋号",
                imo_number="IMO9876543",
                customer_id=customers[0].id,
                vessel_type="散货船"
            ),
            Vessel(
                name="海运之星",
                imo_number="IMO9876544",
                customer_id=customers[0].id,
                vessel_type="集装箱船"
            ),
            Vessel(
                name="招商远航",
                imo_number="IMO9876545",
                customer_id=customers[1].id,
                vessel_type="油轮"
            ),
        ]
        for vessel in vessels:
            db.add(vessel)
        await db.flush()
        
        # ==================== Suppliers ====================
        suppliers = [
            Supplier(
                name="上海船舶配件有限公司",
                code="SHSP",
                type=SupplierType.GOODS,
                contact_person="孙经理",
                contact_phone="13900139001",
                contact_email="sun@shsp.com",
                address="上海市宝山区xxx路",
                is_preferred=True
            ),
            Supplier(
                name="宁波海洋设备厂",
                code="NBHY",
                type=SupplierType.GOODS,
                contact_person="周经理",
                contact_phone="13900139002",
                contact_email="zhou@nbhy.com",
                address="宁波市北仑区xxx路"
            ),
            Supplier(
                name="青岛船舶技术服务",
                code="QDTS",
                type=SupplierType.SERVICE,
                contact_person="郑工",
                contact_phone="13900139003",
                contact_email="zheng@qdts.com",
                address="青岛市市南区xxx路"
            ),
        ]
        for supplier in suppliers:
            db.add(supplier)
        await db.flush()
        
        # ==================== Products ====================
        products = [
            Product(
                name="船用发动机缸套",
                code="ENG-CYL-001",
                specification="MAN B&W 6S50MC-C 型号",
                unit="件",
                brand="MAN",
                category="发动机配件"
            ),
            Product(
                name="船用液压泵",
                code="HYD-PUMP-001",
                specification="压力25MPa，流量200L/min",
                unit="台",
                brand="博世力士乐",
                category="液压设备"
            ),
            Product(
                name="船用阀门",
                code="VALVE-001",
                specification="DN150 PN16 闸阀",
                unit="个",
                brand="上海良工",
                category="阀门"
            ),
            Product(
                name="船用电缆",
                code="CABLE-001",
                specification="CEFR 3*25+1*16",
                unit="米",
                brand="远东电缆",
                category="电气设备"
            ),
            Product(
                name="船用涂料",
                code="PAINT-001",
                specification="环氧防腐漆 20L/桶",
                unit="桶",
                brand="中涂",
                category="涂料"
            ),
        ]
        for product in products:
            db.add(product)
        await db.flush()
        
        # ==================== Supplier Quotes ====================
        supplier_quotes = [
            SupplierQuote(
                supplier_id=suppliers[0].id,
                product_id=products[0].id,
                unit_price=Decimal("45000"),
                currency=Currency.CNY,
                lead_time=30,
                is_preferred=True
            ),
            SupplierQuote(
                supplier_id=suppliers[0].id,
                product_id=products[1].id,
                unit_price=Decimal("28000"),
                currency=Currency.CNY,
                lead_time=20
            ),
            SupplierQuote(
                supplier_id=suppliers[1].id,
                product_id=products[2].id,
                unit_price=Decimal("850"),
                currency=Currency.CNY,
                lead_time=7
            ),
        ]
        for sq in supplier_quotes:
            db.add(sq)
        await db.flush()
        
        # ==================== Node Templates ====================
        # 备件类模板
        spare_parts_templates = [
            NodeTemplate(name="询价确认", project_type=ProjectType.SPARE_PARTS, sort_order=1, default_days=2, is_required=True),
            NodeTemplate(name="报价发送", project_type=ProjectType.SPARE_PARTS, sort_order=2, default_days=1, is_required=True),
            NodeTemplate(name="客户确认", project_type=ProjectType.SPARE_PARTS, sort_order=3, default_days=3, is_required=True),
            NodeTemplate(name="合同签订", project_type=ProjectType.SPARE_PARTS, sort_order=4, default_days=2, is_required=True),
            NodeTemplate(name="采购下单", project_type=ProjectType.SPARE_PARTS, sort_order=5, default_days=1, is_required=True),
            NodeTemplate(name="供应商发货", project_type=ProjectType.SPARE_PARTS, sort_order=6, default_days=10, is_required=True),
            NodeTemplate(name="入库验收", project_type=ProjectType.SPARE_PARTS, sort_order=7, default_days=1, is_required=True),
            NodeTemplate(name="出库发运", project_type=ProjectType.SPARE_PARTS, sort_order=8, default_days=1, is_required=True),
            NodeTemplate(name="客户签收", project_type=ProjectType.SPARE_PARTS, sort_order=9, default_days=2, is_required=True),
            NodeTemplate(name="回款确认", project_type=ProjectType.SPARE_PARTS, sort_order=10, default_days=30, is_required=True),
        ]
        for template in spare_parts_templates:
            db.add(template)
        
        # 技术服务类模板
        tech_service_templates = [
            NodeTemplate(name="需求确认", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=1, default_days=1, is_required=True),
            NodeTemplate(name="方案制定", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=2, default_days=3, is_required=True),
            NodeTemplate(name="报价发送", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=3, default_days=1, is_required=True),
            NodeTemplate(name="合同签订", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=4, default_days=2, is_required=True),
            NodeTemplate(name="人员安排", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=5, default_days=2, is_required=True),
            NodeTemplate(name="现场服务", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=6, default_days=7, is_required=True),
            NodeTemplate(name="验收确认", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=7, default_days=1, is_required=True),
            NodeTemplate(name="回款确认", project_type=ProjectType.TECHNICAL_SERVICE, sort_order=8, default_days=30, is_required=True),
        ]
        for template in tech_service_templates:
            db.add(template)
        await db.flush()
        
        # ==================== Cost Categories ====================
        cost_categories = [
            CostCategory(name="采购成本", code="PROC", sort_order=1),
            CostCategory(name="物流费用", code="LOGISTICS", sort_order=2),
            CostCategory(name="人工费用", code="LABOR", sort_order=3),
            CostCategory(name="税费", code="TAX", sort_order=4),
            CostCategory(name="其他费用", code="OTHER", sort_order=5),
        ]
        for category in cost_categories:
            db.add(category)
        await db.flush()
        
        # ==================== Exchange Rates ====================
        exchange_rates = [
            ExchangeRate(from_currency=Currency.USD, to_currency=Currency.CNY, rate=Decimal("7.2500"), effective_date=date.today()),
            ExchangeRate(from_currency=Currency.EUR, to_currency=Currency.CNY, rate=Decimal("7.8500"), effective_date=date.today()),
            ExchangeRate(from_currency=Currency.JPY, to_currency=Currency.CNY, rate=Decimal("0.0480"), effective_date=date.today()),
            ExchangeRate(from_currency=Currency.HKD, to_currency=Currency.CNY, rate=Decimal("0.9300"), effective_date=date.today()),
        ]
        for rate in exchange_rates:
            db.add(rate)
        await db.flush()
        
        # ==================== Demo Order with Full Workflow ====================
        # Create a demo order
        demo_order = Order(
            order_no="ORD20260108001",
            customer_id=customers[0].id,
            vessel_id=vessels[0].id,
            project_type=ProjectType.SPARE_PARTS,
            status=OrderStatus.IN_PROGRESS,
            currency=Currency.CNY,
            total_amount=Decimal("125000"),
            delivery_date=date.today() + timedelta(days=30),
            pm_id=pm_user.id,
            notes="示例订单 - 远洋号备件采购项目"
        )
        db.add(demo_order)
        await db.flush()
        
        # Order line items
        order_items = [
            OrderLineItem(
                order_id=demo_order.id,
                product_id=products[0].id,
                product_name="船用发动机缸套",
                specification="MAN B&W 6S50MC-C 型号",
                unit="件",
                quantity=Decimal("2"),
                unit_price=Decimal("50000"),
                amount=Decimal("100000")
            ),
            OrderLineItem(
                order_id=demo_order.id,
                product_id=products[2].id,
                product_name="船用阀门",
                specification="DN150 PN16 闸阀",
                unit="个",
                quantity=Decimal("25"),
                unit_price=Decimal("1000"),
                amount=Decimal("25000")
            ),
        ]
        for item in order_items:
            db.add(item)
        await db.flush()
        
        # Create quote
        demo_quote = Quote(
            quote_no="QT-ORD20260108001-V01",
            order_id=demo_order.id,
            version=1,
            status=QuoteStatus.ACCEPTED,
            currency=Currency.CNY,
            total_amount=Decimal("125000"),
            valid_until=date.today() + timedelta(days=30),
            notes="首版报价"
        )
        db.add(demo_quote)
        await db.flush()
        
        # Quote line items
        quote_items = [
            QuoteLineItem(
                quote_id=demo_quote.id,
                product_id=products[0].id,
                product_name="船用发动机缸套",
                specification="MAN B&W 6S50MC-C 型号",
                unit="件",
                quantity=Decimal("2"),
                unit_price=Decimal("50000"),
                amount=Decimal("100000")
            ),
            QuoteLineItem(
                quote_id=demo_quote.id,
                product_id=products[2].id,
                product_name="船用阀门",
                specification="DN150 PN16 闸阀",
                unit="个",
                quantity=Decimal("25"),
                unit_price=Decimal("1000"),
                amount=Decimal("25000")
            ),
        ]
        for item in quote_items:
            db.add(item)
        await db.flush()
        
        # Create contract
        demo_contract = Contract(
            contract_no="CON20260108001",
            order_id=demo_order.id,
            quote_id=demo_quote.id,
            customer_id=customers[0].id,
            title="远洋号备件采购合同",
            status=ContractStatus.EXECUTING,
            currency=Currency.CNY,
            total_amount=Decimal("125000"),
            signed_date=date.today() - timedelta(days=5),
            effective_date=date.today() - timedelta(days=5),
            expiry_date=date.today() + timedelta(days=60),
            payment_terms="预付30%，发货前付40%，验收后付30%"
        )
        db.add(demo_contract)
        await db.flush()
        
        # Payment plans
        payment_plans = [
            PaymentPlan(
                contract_id=demo_contract.id,
                phase="预付款",
                percentage=Decimal("30"),
                planned_amount=Decimal("37500"),
                planned_date=date.today() - timedelta(days=3),
                actual_amount=Decimal("37500"),
                actual_date=date.today() - timedelta(days=3)
            ),
            PaymentPlan(
                contract_id=demo_contract.id,
                phase="发货前付款",
                percentage=Decimal("40"),
                planned_amount=Decimal("50000"),
                planned_date=date.today() + timedelta(days=20)
            ),
            PaymentPlan(
                contract_id=demo_contract.id,
                phase="验收后付款",
                percentage=Decimal("30"),
                planned_amount=Decimal("37500"),
                planned_date=date.today() + timedelta(days=45)
            ),
        ]
        for plan in payment_plans:
            db.add(plan)
        await db.flush()
        
        # ==================== Tracking Nodes for Demo Order ====================
        from app.models.tracking import TrackingNode, NodeStatus
        
        tracking_nodes = [
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[0].id,
                name="询价确认",
                status=NodeStatus.COMPLETED,
                planned_date=date.today() - timedelta(days=10),
                actual_date=date.today() - timedelta(days=10),
                sort_order=1
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[1].id,
                name="报价发送",
                status=NodeStatus.COMPLETED,
                planned_date=date.today() - timedelta(days=9),
                actual_date=date.today() - timedelta(days=9),
                sort_order=2
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[2].id,
                name="客户确认",
                status=NodeStatus.COMPLETED,
                planned_date=date.today() - timedelta(days=6),
                actual_date=date.today() - timedelta(days=6),
                sort_order=3
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[3].id,
                name="合同签订",
                status=NodeStatus.COMPLETED,
                planned_date=date.today() - timedelta(days=4),
                actual_date=date.today() - timedelta(days=5),
                sort_order=4
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[4].id,
                name="采购下单",
                status=NodeStatus.IN_PROGRESS,
                planned_date=date.today() - timedelta(days=3),
                sort_order=5,
                assignee_id=users[2].id  # proc user
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[5].id,
                name="供应商发货",
                status=NodeStatus.OVERDUE,
                planned_date=date.today() - timedelta(days=3),
                sort_order=6
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[6].id,
                name="入库验收",
                status=NodeStatus.PENDING,
                planned_date=date.today() + timedelta(days=7),
                sort_order=7
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[7].id,
                name="出库发运",
                status=NodeStatus.PENDING,
                planned_date=date.today() + timedelta(days=8),
                sort_order=8
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[8].id,
                name="客户签收",
                status=NodeStatus.PENDING,
                planned_date=date.today() + timedelta(days=10),
                sort_order=9
            ),
            TrackingNode(
                order_id=demo_order.id,
                template_id=spare_parts_templates[9].id,
                name="回款确认",
                status=NodeStatus.PENDING,
                planned_date=date.today() + timedelta(days=40),
                sort_order=10
            ),
        ]
        for node in tracking_nodes:
            db.add(node)
        await db.flush()
        
        # ==================== Procurement for Demo Order ====================
        from app.models.procurement import Procurement, ProcurementLineItem, ProcurementStatus
        
        demo_procurement = Procurement(
            procurement_no="PO20260108001",
            order_id=demo_order.id,
            supplier_id=suppliers[0].id,
            status=ProcurementStatus.PENDING_APPROVAL,
            currency=Currency.CNY,
            total_amount=Decimal("90000"),
            expected_date=date.today() + timedelta(days=10),
            created_by=users[2].id,  # proc user
            notes="供应商：上海船舶配件有限公司"
        )
        db.add(demo_procurement)
        await db.flush()
        
        procurement_items = [
            ProcurementLineItem(
                procurement_id=demo_procurement.id,
                product_id=products[0].id,
                product_name="船用发动机缸套",
                specification="MAN B&W 6S50MC-C 型号",
                unit="件",
                quantity=Decimal("2"),
                unit_price=Decimal("45000"),
                amount=Decimal("90000")
            ),
        ]
        for item in procurement_items:
            db.add(item)
        await db.flush()
        
        # Create another order for more demo data
        demo_order2 = Order(
            order_no="ORD20260107002",
            customer_id=customers[1].id,
            vessel_id=vessels[2].id,
            project_type=ProjectType.SPARE_PARTS,
            status=OrderStatus.IN_PROGRESS,
            currency=Currency.USD,
            total_amount=Decimal("35000"),
            delivery_date=date.today() + timedelta(days=45),
            pm_id=pm_user.id,
            notes="招商远航号备件采购项目"
        )
        db.add(demo_order2)
        await db.flush()
        
        # ==================== Ship Repair Module Demo Data ====================
        try:
            from app.models.ship_repair import (
                RepairPlan, RepairTask, DailyReport, NCR, SparePartRisk
            )
        except ImportError as exc:
            print(f"Ship repair demo seed skipped: {exc}")
        else:
            # Create ship repair order
            ship_repair_order = Order(
                order_no="ORD20260601001",
                customer_id=customers[0].id,
                vessel_id=vessels[0].id,
                project_type=ProjectType.SHIP_REPAIR,
                status=OrderStatus.IN_PROGRESS,
                currency=Currency.CNY,
                total_amount=Decimal("2800000"),
                delivery_date=date.today() + timedelta(days=25),
                pm_id=pm_user.id,
                notes="远洋号坞修项目 - 主机大修、船体除锈涂装"
            )
            db.add(ship_repair_order)
            await db.flush()

            # Repair Plan with plan_text for AI disassembly
            repair_plan = RepairPlan(
                order_id=ship_repair_order.id,
                source="SHIPOWNER",
                version="v1.0",
                uploaded_by=pm_user.id,
                plan_name="远洋号坞修计划 2026年6月",
                plan_text="""船舶维修需求清单:
1. 主机大修：拆检主机缸套、活塞、轴承，更换磨损件，预计需要7天
2. 船体除锈涂装：水线以下区域Sa2.5级喷砂除锈，涂刷环氧底漆和防污漆，预计需要5天
3. 舵机维护保养：检查液压系统，更换密封件，测试舵角，预计需要2天
4. 锚机检修：拆检锚机齿轮箱，更换润滑油，测试功能，预计需要1天
5. 救生设备检验：救生艇、救生筏、救生衣等按规范检验，预计需要1天
6. 消防系统维护：检查消防泵、管路、喷头，功能测试，预计需要1天
7. 电气系统检查：主配电板、应急发电机、航行灯等检查维护，预计需要2天
8. 甲板设备保养：绞缆机、克令吊等甲板机械检查保养，预计需要2天

总预计工期：25天""",
                plan_duration_days=25,
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=28),
                notes="船东要求6月15日前完工",
                ai_disassembled=False,
                human_confirmed=False
            )
            db.add(repair_plan)
            await db.flush()

            # Another repair plan that's already confirmed (to show different states)
            repair_plan_confirmed = RepairPlan(
                order_id=ship_repair_order.id,
                source="INTERNAL",
                version="v0.9",
                uploaded_by=pm_user.id,
                plan_name="初步修船计划（已确认）",
                plan_text="简要修船计划：主机检修、船体涂装",
                plan_duration_days=20,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=20),
                ai_disassembled=True,
                human_confirmed=True,
                ai_task_output={"summary": "已拆解为8个主要任务", "tasks": []}
            )
            db.add(repair_plan_confirmed)
            await db.flush()

            # Daily Report
            daily_report = DailyReport(
                order_id=ship_repair_order.id,
                report_date=date.today(),
                reporter_id=pm_user.id,
                site_status="HAS_RISK",
                completed_tasks="完成主机缸套拆检，发现2号缸磨损较严重；完成船体水线以下30%除锈作业",
                unfinished_tasks="主机活塞检查因工具未到位推迟；舵机液压系统发现漏油需要处理",
                unfinished_reason="SPARE_PART_MISSING",
                affects_schedule=True,
                estimated_delay_days=2,
                affects_quality=False,
                affects_safety=False,
                requires_gm_decision=True,
                gm_decision_items="是否同时更换1号缸和3号缸的缸套（船东未明确要求但建议更换）",
                one_line_summary="进度正常但存在备件短缺和设备漏油问题",
                notes="明天需要协调备件采购和液压维修工"
            )
            db.add(daily_report)
            await db.flush()

            # NCR 1 - Active, no root cause yet
            ncr1 = NCR(
                ncr_number=f"NCR-{date.today().strftime('%Y%m%d')}-001",
                order_id=ship_repair_order.id,
                issue_description="舵机液压系统发现漏油，漏油点位于液压缸与管路连接处，现场已用临时容器收集漏油。检查发现密封圈老化严重，需要立即更换。漏油量约500ml/小时，如不及时处理可能导致液压系统失效，影响舵机正常工作。",
                discovered_by=pm_user.id,
                discovered_date=date.today(),
                responsible_party="SHIPYARD",
                status="PENDING"
            )
            db.add(ncr1)
            await db.flush()

            # NCR 2 - Has root cause, pending rectification
            ncr2 = NCR(
                ncr_number=f"NCR-{date.today().strftime('%Y%m%d')}-002",
                order_id=ship_repair_order.id,
                issue_description="主机2号缸缸套内壁发现异常磨损，磨损深度超过规范允许值0.5mm，磨损位置集中在活塞上止点附近，呈椭圆形磨损痕迹。",
                discovered_by=pm_user.id,
                discovered_date=date.today() - timedelta(days=1),
                responsible_party="INTERNAL",
                root_cause_analysis="初步分析认为是长期使用劣质润滑油导致润滑不足，加上冷却水温度控制不当造成局部高温，加速了缸套磨损。此外活塞环可能也存在磨损或卡滞现象。",
                status="IN_PROGRESS"
            )
            db.add(ncr2)
            await db.flush()

            # NCR 3 - Complete with rectification
            ncr3 = NCR(
                ncr_number=f"NCR-{date.today().strftime('%Y%m%d')}-003",
                order_id=ship_repair_order.id,
                issue_description="船体除锈作业中发现左舷水线下方约2平方米区域钢板减薄严重，测厚仪显示厚度仅为原设计厚度的60%，存在结构强度隐患。",
                discovered_by=pm_user.id,
                discovered_date=date.today() - timedelta(days=3),
                responsible_party="SHIPYARD",
                root_cause_analysis="该区域长期受海水腐蚀，加上该部位为污水舱外板，内部污水酸性较强，造成内外双重腐蚀。日常检查中未能及时发现并采取防护措施。",
                rectification_measures="已联系船厂焊工，计划采用局部换板方式处理。切除减薄板材约2.5平方米，更换为8mm新钢板，按船级社规范要求进行焊接和探伤检验。",
                planned_completion_date=date.today() + timedelta(days=5),
                status="PENDING_REVIEW"
            )
            db.add(ncr3)
            await db.flush()

            # Spare Part Risk
            spare_risk = SparePartRisk(
                risk_number=f"RISK-{date.today().strftime('%Y%m%d')}-001",
                order_id=ship_repair_order.id,
                spare_part_name="主机缸套",
                model_specification="MAN B&W 6S50MC-C 型号 Φ500x850mm",
                quantity=1,
                unit="件",
                belonging_equipment_system="主机系统",
                installation_location="2号缸",
                affects_schedule=True,
                estimated_delay_days=7,
                urgency="HIGH",
                demand_reason="NCR-20260609-002中发现2号缸缸套磨损超标，必须更换。该备件交货期较长，需立即启动采购。",
                supervisor_notes="已联系3家供应商询价，预计交货期最快7天（空运）。建议同时订购1号和3号缸备用缸套。",
                expected_arrival_date=date.today() + timedelta(days=7),
                submitted_by=pm_user.id,
                status="DRAFT"
            )
            db.add(spare_risk)
            await db.flush()
        
        await db.commit()
        print("✅ Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
