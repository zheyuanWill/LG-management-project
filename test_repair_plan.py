
import httpx
import json
import sys
import asyncio

async def test_repair_plan():
    base_url = "http://localhost:8000/api"
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            print("=" * 80)
            print("STEP 1: 登录系统")
            print("=" * 80)
            
            login_resp = await client.post(
                f"{base_url}/auth/login",
                json={"username": "pm", "password": "123456"}
            )
            print(f"登录状态码: {login_resp.status_code}")
            if login_resp.status_code != 200:
                print(f"登录错误: {login_resp.text}")
                return
            login_data = login_resp.json()
            token = login_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✅ 登录成功，Token已获取")
            
            print("\n" + "=" * 80)
            print("STEP 2: 获取订单列表，选一个关联")
            print("=" * 80)
            orders_resp = await client.get(f"{base_url}/orders", headers=headers)
            print(f"获取订单状态: {orders_resp.status_code}")
            if orders_resp.status_code == 200:
                orders_data = orders_resp.json()
                print(f"订单数量: {orders_data.get('total', 0)}")
                order_id = None
                if orders_data.get("items"):
                    order_id = orders_data["items"][0]["id"]
                    print(f"使用订单ID: {order_id}")
                else:
                    print("⚠️  没有订单，将创建不带order_id的计划")
            else:
                order_id = None
                print(f"⚠️  无法获取订单，错误: {orders_resp.text}")
            
            print("\n" + "=" * 80)
            print("STEP 3: 创建修船计划")
            print("=" * 80)
            
            plan_text = """远洋号年度检修计划

一、船体部分（10天）
1. 进坞与定位
2. 船体外部检查与测量
3. 船底除锈与涂装
4. 水线以上涂层保养
5. 螺旋桨与舵系检查
6. 海底阀箱清洁与检查
7. 船体内部舱室检查

二、主机与辅机部分（15天）
1. 主机吊缸检修
2. 活塞与缸套检查
3. 喷油器校验
4. 增压器检修
5. 滑油系统清洗
6. 冷却系统检查
7. 发电机检修与负载试验
8. 空压机保养

三、电气系统（8天，可并行）
1. 主配电板检修
2. 电缆绝缘测试
3. 航行设备校验
4. 通信设备检查
5. 照明系统检修

四、坞内工程（10天，与部分船体工程并行）
1. 船舶测厚
2. 船级社检验
3. 艉轴抽出检查

五、收尾与试航（5天）
1. 系泊试验
2. 航行试验
3. 完工文件整理
4. 交船

计划总工期：30天

重点关注：
- 主机第3缸和第5缸磨损情况
- 海底阀箱防腐
- 电气系统绝缘
"""
            
            plan_payload = {
                "plan_name": "远洋号年度检修计划",
                "version": "V1.0",
                "source": "INTERNAL",
                "plan_duration_days": 30,
                "plan_text": plan_text,
                "status": "DRAFT"
            }
            
            if order_id:
                plan_payload["order_id"] = order_id
            
            create_resp = await client.post(
                f"{base_url}/ship-repair/repair-plans",
                json=plan_payload,
                headers=headers
            )
            
            print(f"创建计划状态码: {create_resp.status_code}")
            if create_resp.status_code != 200:
                print(f"创建计划错误: {create_resp.text}")
                return
            plan_data = create_resp.json()
            plan_id = plan_data["id"]
            print(f"✅ 计划创建成功")
            print(f"   - 计划ID: {plan_id}")
            print(f"   - 计划名称: {plan_data['plan_name']}")
            
            print("\n" + "=" * 80)
            print("STEP 4: AI拆解计划")
            print("=" * 80)
            print(f"调用AI拆解API ({plan_id})...")
            
            ai_resp = await client.post(
                f"{base_url}/ship-repair/repair-plans/{plan_id}/ai-disassemble",
                json={
                    "plan_text": plan_text,
                    "plan_duration_days": 30
                },
                headers=headers
            )
            
            print(f"AI拆解状态码: {ai_resp.status_code}")
            if ai_resp.status_code != 200:
                print(f"AI拆解错误: {ai_resp.text}")
                return
            
            ai_result = ai_resp.json()
            print("\n" + "=" * 80)
            print("✅ AI拆解成功！")
            print("=" * 80)
            print(f"\n摘要: {ai_result.get('summary', 'N/A')}")
            
            tasks = ai_result.get("tasks", [])
            print(f"\n拆解出 {len(tasks)} 个任务:\n")
            
            for i, task in enumerate(tasks, 1):
                print(f"{i}. {task['task_name']}")
                print(f"   - 工期: {task['estimated_days']} 天")
                print(f"   - 分类: {task['category']}")
                print(f"   - 负责人: {task.get('responsible_party', 'N/A')}")
                print(f"   - 关键路径: {'是' if task.get('critical_path', False) else '否'}")
                if task.get("sub_tasks"):
                    print(f"   - 子任务:")
                    for st in task["sub_tasks"]:
                        print(f"     * {st}")
                print()
            
            print("\n" + "=" * 80)
            print("🎉 测试成功！你现在可以在前端页面查看结果了")
            print("=" * 80)
            print("\n前端地址: http://localhost:3000")
            
    except Exception as e:
        print(f"❌ 测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试修船计划AI拆解功能...\n")
    asyncio.run(test_repair_plan())

