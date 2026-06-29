"""
直接调用金蝶原始 API 并打印完整返回值
运行: python test_kingdee_raw.py
"""
import asyncio
import json
from app.integrations.kingdee.client import get_kingdee_client, KingdeeAPIError

ERROR_CODES = {
    0: "成功",
    -2: "失败",
    40000: "未提供用户名参数",
    40001: "无API访问权限",
    40002: "无精斗云服务访问权限",
    40003: "无账套访问权限",
    40202: "无会计科目新增权限",
    42020: "未提供dbId参数",
    42021: "dbId参数格式非法",
    42022: "dbId对应的账套不存在或无权限",
    42030: "未提供sId参数",
    42031: "sId参数格式错误",
    42032: "sId对应的服务不存在",
    42033: "用户无sId对应的服务的使用权限",
    42034: "sId对应的服务不存在或者无法访问",
    42035: "sId对应的服务不属于会计服务类型",
    46001: "数据验证不通过",
    46002: "暂无查询结果",
    46003: "操作记录数为0",
    46004: "批量操作记录数超限200",
    48001: "未预期的错误",
    48002: "不支持的接口请求方式",
}


def explain_code(code):
    try:
        c = int(code)
    except (ValueError, TypeError):
        return f"未知错误码: {code}"
    return ERROR_CODES.get(c, f"未知错误码: {c}")


async def main():
    client = get_kingdee_client()

    print("=" * 60)
    print("金蝶原始 API 测试")
    print(f"Base URL: {client.base_url}")
    print(f"sId: {client.sid}")
    print(f"dbId: {client.db_id}")
    print("=" * 60)

    apis = [
        ("凭证查询", "POST", "/jdyaccouting/voucherlist",
         {"fromPeriod": 202601, "toPeriod": 202612, "page": 1, "pageSize": 5}),
        ("凭证汇总", "GET", "/jdyaccouting/voucher?action=getVchTotalQuery&fromDate=202601&toDate=202612", None),
        ("科目余额表", "GET", "/jdyaccouting/account/balance", None),
        ("总账", "GET", "/jdyaccouting/report/genledger?fromPeriod=202601&toPeriod=202612", None),
        ("明细账", "GET", "/jdyaccouting/querydetail?accountNum=1001&fromPeriod=202601&toPeriod=202612", None),
        ("利润表", "GET", "/jdyaccouting/report?reportType=2&startPeriod=202601&endPeriod=202603", None),
        ("资产负债表", "GET", "/jdyaccouting/report?reportType=1&startPeriod=202601&endPeriod=202603", None),
        ("现金流量表", "GET", "/jdyaccouting/report?reportType=3&startPeriod=202601&endPeriod=202603", None),
        ("出纳日记账", "GET", "/jdyaccouting/cashier/journal/list?fromPeriod=202601&toPeriod=202612", None),
        ("出纳账户", "GET", "/jdyaccouting/cashieraccount/list", None),
    ]

    for name, method, path, body in apis:
        print(f"\n{'─' * 50}")
        print(f"【{name}】 {method} {path}")
        try:
            if method == "POST":
                result = await client.post(path, json=body)
            else:
                result = await client.get(path)

            code = result.get("code", result.get("status", "N/A"))
            print(f"  返回码: {code} → {explain_code(code)}")
            print(f"  完整返回: {json.dumps(result, ensure_ascii=False, indent=2)[:1000]}")
        except KingdeeAPIError as e:
            print(f"  异常码: {e.code} → {explain_code(e.code)}")
            print(f"  异常消息: {e.message}")
            if e.response:
                print(f"  原始响应: {json.dumps(e.response, ensure_ascii=False, indent=2)[:500]}")
        except Exception as e:
            print(f"  未知异常: {type(e).__name__}: {e}")

    await client.close()
    print(f"\n{'=' * 60}")
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())
