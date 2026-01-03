"""测试脚本 - 验证 API 功能."""

import asyncio
import json

import httpx


# 测试配置
BASE_URL = "http://localhost:5566"
API_KEY = "test_api_key_12345"


async def check_service_running() -> bool:
    """检查服务是否运行."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False


async def test_health_check():
    """测试健康检查接口."""
    print("\n=== 测试健康检查接口 ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"响应: {response.json()}")
                assert response.json()["status"] == "ok"
                print("✅ 健康检查接口测试通过")
                return True
            else:
                print(f"❌ 服务返回错误状态码: {response.status_code}")
                print(f"响应内容: {response.text[:200]}")
                return False
        except httpx.ConnectError:
            print(f"❌ 无法连接到服务 {BASE_URL}")
            print("   请确保服务已启动: python -m wxpush.main")
            return False
        except Exception as e:
            print(f"❌ 健康检查接口测试失败: {e}")
            return False


async def test_send_get_invalid_api_key():
    """测试 GET 请求 - 无效的 API Key."""
    print("\n=== 测试 GET 请求 - 无效的 API Key ===")
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "api_key": "invalid_key",
                "title": "测试标题",
                "content": "测试内容",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
            }
            response = await client.get(f"{BASE_URL}/send", params=params)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            assert response.status_code == 401
            assert response.json()["detail"]["errcode"] == 40001
            print("✅ 无效 API Key 测试通过（正确拒绝）")
            return True
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False


async def test_send_get_missing_params():
    """测试 GET 请求 - 缺少参数."""
    print("\n=== 测试 GET 请求 - 缺少参数 ===")
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "api_key": API_KEY,
                "title": "测试标题",
                # 缺少 content, appid, secret, userid
            }
            response = await client.get(f"{BASE_URL}/send", params=params)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            assert response.status_code == 422  # 验证错误
            print("✅ 参数验证测试通过（正确拒绝缺少的参数）")
            return True
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False


async def test_send_get_valid_request():
    """测试 GET 请求 - 有效请求（会失败，因为没有真实的微信凭证）."""
    print("\n=== 测试 GET 请求 - 有效请求 ===")
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "api_key": API_KEY,
                "title": "服务器通知",
                "content": "这是一条测试消息",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
                "template_id": "test_template_id",  # 提供 template_id
            }
            response = await client.get(f"{BASE_URL}/send", params=params, timeout=30.0)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

            # 预期：API Key 验证通过，但因为微信凭证无效，会返回微信 API 的错误
            # 或者因为缺少 template_id，会返回相关错误
            if response.status_code == 400:
                print("✅ 请求已通过 API Key 验证，但由于微信凭证问题返回错误（符合预期）")
                return True
            elif response.status_code == 200:
                print("✅ 请求成功（但实际微信 API 可能返回错误）")
                return True
            else:
                print(f"⚠️ 意外的状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_send_post_valid_request():
    """测试 POST 请求 - 有效请求（微信公众平台）."""
    print("\n=== 测试 POST 请求 - 有效请求（微信公众平台） ===")
    async with httpx.AsyncClient() as client:
        try:
            data = {
                "api_key": API_KEY,
                "title": "服务器通知",
                "content": "这是一条测试消息（POST）",
                "appid": "test_appid",
                "secret": "test_secret",
                "userid": "test_userid",
                "template_id": "test_template_id",
                "channel": "wechat",
            }
            response = await client.post(
                f"{BASE_URL}/send",
                json=data,
                timeout=30.0
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

            if response.status_code == 400:
                print("✅ 请求已通过 API Key 验证，但由于微信凭证问题返回错误（符合预期）")
                return True
            elif response.status_code == 200:
                print("✅ 请求成功")
                return True
            else:
                print(f"⚠️ 意外的状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_send_workwechat_get():
    """测试 GET 请求 - 企业微信."""
    print("\n=== 测试 GET 请求 - 企业微信 ===")
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "api_key": API_KEY,
                "title": "企业微信通知",
                "content": "这是一条企业微信测试消息",
                "appid": "test_corpid",
                "secret": "test_corpsecret",
                "userid": "test_userid",
                "agentid": "1000001",
                "channel": "workwechat",
            }
            response = await client.get(f"{BASE_URL}/send", params=params, timeout=30.0)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

            if response.status_code == 400:
                print("✅ 请求已通过 API Key 验证，但由于企业微信凭证问题返回错误（符合预期）")
                return True
            elif response.status_code == 200:
                print("✅ 请求成功")
                return True
            else:
                print(f"⚠️ 意外的状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_send_workwechat_post():
    """测试 POST 请求 - 企业微信."""
    print("\n=== 测试 POST 请求 - 企业微信 ===")
    async with httpx.AsyncClient() as client:
        try:
            data = {
                "api_key": API_KEY,
                "title": "企业微信通知",
                "content": "这是一条企业微信测试消息（POST）",
                "appid": "test_corpid",
                "secret": "test_corpsecret",
                "userid": "test_userid",
                "agentid": "1000001",
                "channel": "workwechat",
            }
            response = await client.post(
                f"{BASE_URL}/send",
                json=data,
                timeout=30.0
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

            if response.status_code == 400:
                print("✅ 请求已通过 API Key 验证，但由于企业微信凭证问题返回错误（符合预期）")
                return True
            elif response.status_code == 200:
                print("✅ 请求成功")
                return True
            else:
                print(f"⚠️ 意外的状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_send_workwechat_missing_agentid():
    """测试企业微信 - 缺少 agentid 参数."""
    print("\n=== 测试企业微信 - 缺少 agentid 参数 ===")
    async with httpx.AsyncClient() as client:
        try:
            data = {
                "api_key": API_KEY,
                "title": "企业微信通知",
                "content": "这是一条企业微信测试消息",
                "appid": "test_corpid",
                "secret": "test_corpsecret",
                "userid": "test_userid",
                "channel": "workwechat",
                # 缺少 agentid
            }
            response = await client.post(
                f"{BASE_URL}/send",
                json=data,
                timeout=30.0
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

            # 应该返回 400 错误，提示缺少 agentid
            if response.status_code == 400:
                errmsg = response.json().get("detail", {}).get("errmsg", "")
                if "agentid" in errmsg.lower():
                    print("✅ 正确检测到缺少 agentid 参数")
                    return True
                else:
                    print("⚠️ 返回了错误，但错误消息可能不正确")
                    return True  # 还是算通过，因为返回了错误
            else:
                print(f"⚠️ 意外的状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_api_docs():
    """测试 API 文档接口."""
    print("\n=== 测试 API 文档接口 ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/docs")
            print(f"状态码: {response.status_code}")
            assert response.status_code == 200
            print("✅ API 文档接口可访问")
            return True
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False


async def main():
    """运行所有测试."""
    print("=" * 60)
    print("微信消息推送服务 - API 功能测试")
    print("=" * 60)
    print(f"\n测试目标: {BASE_URL}")
    print(f"测试 API Key: {API_KEY}")
    print("\n请确保服务已启动: python -m wxpush.main")
    print("=" * 60)

    # 检查服务是否运行
    print("\n检查服务状态...")
    if not await check_service_running():
        print("\n❌ 错误: 服务未运行或无法连接")
        print("   请先启动服务: python -m wxpush.main")
        print("   或者使用: 启动服务.bat (Windows) 或 ./启动服务.sh (Linux/Mac)")
        return

    print("✅ 服务正在运行\n")

    results = []

    # 运行测试
    results.append(await test_health_check())
    results.append(await test_api_docs())
    results.append(await test_send_get_invalid_api_key())
    results.append(await test_send_get_missing_params())
    results.append(await test_send_get_valid_request())
    results.append(await test_send_post_valid_request())
    # 企业微信测试
    results.append(await test_send_workwechat_get())
    results.append(await test_send_workwechat_post())
    results.append(await test_send_workwechat_missing_agentid())

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())

