
import asyncio
import httpx
import sys
from datetime import datetime, date

BASE_URL = "http://localhost:8000/api"

async def test_ship_repair_loopback():
    print("开始修船监修业务闭环测试...")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. 登录 (使用 OWNER 账号)
        print("\n1. 登录验证...")
        login_resp = await client.post("/auth/login", json={
            "username": "owner",
            "password": "123456"
        })
        if login_resp.status_code != 200:
            print(f"登录失败: {login_resp.text}")
            return
        
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("登录成功")

        # 获取一个订单 ID
        print("\n2. 获取基础数据...")
        orders_resp = await client.get("/orders", headers=headers, params={"size": 1})
        if orders_resp.status_code != 200 or not orders_resp.json()["items"]:
            print("未发现订单数据，请确保数据库已初始化")
            return
        order_id = orders_resp.json()["items"][0]["id"]
        print(f"使用订单 ID: {order_id}")

        # 3. 测试监修日报闭环...
        print("\n3. 测试监修日报闭环...")
        daily_report_data = {
            "order_id": order_id,
            "report_date": date.today().isoformat(),
            "reporter_id": 1,
            "site_status": "NORMAL",
            "completed_tasks": "更换主机缸套",
            "unfinished_tasks": "测试主机运行",
            "unfinished_reason": "OTHER",
            "affects_schedule": True,
            "estimated_delay_days": 2,
            "affects_quality": False,
            "affects_safety": False,
            "requires_gm_decision": True,
            "gm_decision_items": "是否需要紧急采购备件 A？",
            "one_line_summary": "现场有风险，需关注备件情况"
        }
        dr_resp = await client.post("/api/ship-repair/daily-reports", json=daily_report_data, headers=headers)
        if dr_resp.status_code != 200:
            print(f"创建日报失败 ({dr_resp.status_code}): {dr_resp.text}")
        else:
            dr_id = dr_resp.json()["id"]
            print(f"日报创建成功，ID: {dr_id}")

        # 4. 测试异常转 NCR 闭环
        print("\n4. 测试异常(Anomaly)转 NCR 闭环...")
        anomaly_data = {
            "order_id": order_id,
            "anomaly_type": "QUALITY_ISSUE",
            "description": "焊接点不合格",
            "impact_scope": "局部",
            "affects_schedule": False,
            "affects_quality": True,
            "affects_safety": False,
            "status": "PENDING",
            "reported_by": 1 # Owner
        }
        anom_resp = await client.post("/api/ship-repair/anomalies", json=anomaly_data, headers=headers)
        if anom_resp.status_code != 200:
            print(f"创建异常失败 ({anom_resp.status_code}): {anom_resp.text}")
        else:
            anom_id = anom_resp.json()["id"]
            print(f"异常创建成功，ID: {anom_id}")
            
            # 转 NCR
            ncr_number = f"NCR-TEST-{datetime.now().strftime('%H%M%S')}"
            convert_resp = await client.post(f"/api/ship-repair/anomalies/{anom_id}/convert-to-ncr", 
                                          json={"ncr_number": ncr_number}, headers=headers)
            if convert_resp.status_code == 200:
                # convert_to_ncr returns the updated anomaly
                ncr_id = convert_resp.json()["converted_to_ncr_id"]
                print(f"成功转换为 NCR, ID: {ncr_id}, 编号: {ncr_number}")
                
                # NCR 流程：添加原因 -> 添加整改 -> 提交复查 -> 复查通过
                await client.post(f"/api/ship-repair/ncrs/{ncr_id}/add-root-cause", 
                                json={"root_cause_analysis": "操作工培训不足"}, headers=headers)
                await client.post(f"/api/ship-repair/ncrs/{ncr_id}/add-rectification", 
                                json={"rectification_measures": "重新焊接并加强培训", "planned_completion_date": date.today().isoformat()}, headers=headers)
                await client.post(f"/api/ship-repair/ncrs/{ncr_id}/submit-for-review", json={}, headers=headers)
                review_resp = await client.post(f"/api/ship-repair/ncrs/{ncr_id}/review", 
                                             json={"review_result": "合格", "is_approved": True}, headers=headers)
                if review_resp.status_code == 200:
                    print(f"NCR 闭环流程完成，最终状态: {review_resp.json()['status']}")
                else:
                    print(f"NCR 复查失败 ({review_resp.status_code}): {review_resp.text}")
            else:
                print(f"转 NCR 失败 ({convert_resp.status_code}): {convert_resp.text}")

        # 5. 测试缺备件风险闭环
        print("\n5. 测试缺备件风险(SparePartRisk)闭环...")
        risk_data = {
            "risk_number": f"RISK-TEST-{datetime.now().strftime('%H%M%S')}",
            "order_id": order_id,
            "spare_part_name": "主机活塞环",
            "quantity": 6,
            "unit": "Pcs",
            "urgency": "HIGH",
            "status": "DRAFT",
            "submitted_by": 1
        }
        risk_resp = await client.post("/api/ship-repair/spare-part-risks", json=risk_data, headers=headers)
        if risk_resp.status_code != 200:
            print(f"创建风险单失败 ({risk_resp.status_code}): {risk_resp.text}")
        else:
            risk_id = risk_resp.json()["id"]
            print(f"风险单创建成功，ID: {risk_id}")
            
            # 提交审批
            await client.post(f"/api/ship-repair/spare-part-risks/{risk_id}/submit", json={}, headers=headers)
            # 审批通过
            await client.post(f"/api/ship-repair/spare-part-risks/{risk_id}/approve", 
                            json={"approval_opinion": "同意采购"}, headers=headers)
            # 推送供应商
            await client.post(f"/api/ship-repair/spare-part-risks/{risk_id}/push-to-suppliers", 
                            json={}, headers=headers)
            # 标记反馈已收到
            await client.post(f"/api/ship-repair/spare-part-risks/{risk_id}/feedback-received", json={}, headers=headers)
            # 最终审核
            final_resp = await client.post(f"/api/ship-repair/spare-part-risks/{risk_id}/review-feedback", 
                                        json={"review_opinion": "反馈符合预期，请下单"}, headers=headers)
            if final_resp.status_code == 200:
                print(f"风险单流程完成，最终状态: {final_resp.json()['status']}")
            else:
                print(f"风险单最终审核失败 ({final_resp.status_code}): {final_resp.text}")

    print("\n测试完成。")

if __name__ == "__main__":
    asyncio.run(test_ship_repair_loopback())
