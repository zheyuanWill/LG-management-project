
import httpx
import json
from datetime import datetime, timedelta

async def test_repair_plan_ai_breakdown():
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # 1. Login
            login_response = await client.post(
                'http://localhost:8000/api/auth/login',
                json={'username': 'pm', 'password': '123456'}
            )
            login_data = login_response.json()
            token = login_data['access_token']
            print('✅ Login successful')
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # 2. Check if we have existing repair plans
            plans_response = await client.get(
                'http://localhost:8000/api/ship-repair/repair-plans',
                headers=headers
            )
            print(f'✅ Repair plans status: {plans_response.status_code}')
            
            # 3. If no plans, create a test one
            if plans_response.status_code == 200:
                plans_data = plans_response.json()
                if plans_data.get('total', 0) == 0 or not plans_data.get('items'):
                    print('📝 Creating test repair plan...')
                    create_response = await client.post(
                        'http://localhost:8000/api/ship-repair/repair-plans',
                        json={
                            'plan_name': '远洋号年度检修计划',
                            'version': 'V1.0',
                            'source': 'INTERNAL',
                            'plan_duration_days': 30,
                            'plan_start_date': '2026-06-10',
                            'plan_end_date': '2026-07-10',
                            'plan_text': '''远洋号年度检修计划

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
开始时间：2026-06-10
结束时间：2026-07-10

重点关注：
- 主机第3缸和第5缸磨损情况
- 海底阀箱防腐
- 电气系统绝缘'''
                        },
                        headers=headers
                    )
                    print(f'✅ Create plan response: {create_response.status_code}')
                    print(json.dumps(create_response.json(), indent=2, ensure_ascii=False))
            
            # 4. Get plans again
            plans_response = await client.get(
                'http://localhost:8000/api/ship-repair/repair-plans',
                headers=headers
            )
            plans_data = plans_response.json()
            if plans_data.get('items'):
                plan = plans_data['items'][0]
                plan_id = plan['id']
                print(f'\n🎯 Testing AI breakdown on plan ID: {plan_id}')
                print(f'   Plan name: {plan["plan_name"]}')
                print(f'   Plan duration: {plan["plan_duration_days"]} days')
                
                # 5. Test AI breakdown
                print('\n🔄 Running AI breakdown...')
                ai_response = await client.post(
                    f'http://localhost:8000/api/ship-repair/repair-plans/{plan_id}/ai-disassemble',
                    json={
                        'plan_text': plan['plan_text'],
                        'plan_duration_days': plan['plan_duration_days']
                    },
                    headers=headers
                )
                print(f'✅ AI breakdown status: {ai_response.status_code}')
                ai_result = ai_response.json()
                print('\n🎉 AI拆解成功！结果：')
                print(f'   Summary: {ai_result.get("summary")}')
                print(f'   Tasks generated: {len(ai_result.get("tasks", []))}')
                print('\n📋 拆解出的任务：')
                for i, task in enumerate(ai_result.get('tasks', [])):
                    print(f'   {i+1}. {task["task_name"]} ({task["estimated_days"]}天, {task["category"]})')
                    if task.get('sub_tasks'):
                        for st in task['sub_tasks'][:2]:
                            print(f'      - {st}')
                        if len(task['sub_tasks']) > 2:
                            print(f'      ... 还有{len(task["sub_tasks"])-2}个子任务')
                return ai_result
            
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_repair_plan_ai_breakdown())

