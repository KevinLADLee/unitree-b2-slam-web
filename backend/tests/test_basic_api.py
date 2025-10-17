"""
基础 API 测试

验证 FastAPI 应用的基本功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    print("\n【测试1】根路径 GET /")
    response = client.get("/")
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.json()}")
    assert response.status_code == 200
    assert response.json()["service"] == "Unitree B2 SLAM Backend"
    print("  ✅ 通过")


def test_health_check():
    """测试健康检查"""
    print("\n【测试2】健康检查 GET /health")
    response = client.get("/health")
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("  ✅ 通过")


def test_docs():
    """测试 API 文档"""
    print("\n【测试3】API 文档 GET /docs")
    response = client.get("/docs")
    print(f"  状态码: {response.status_code}")
    assert response.status_code == 200
    print("  ✅ Swagger UI 可访问")


def test_openapi():
    """测试 OpenAPI schema"""
    print("\n【测试4】OpenAPI Schema GET /openapi.json")
    response = client.get("/openapi.json")
    print(f"  状态码: {response.status_code}")
    assert response.status_code == 200
    schema = response.json()
    print(f"  API 标题: {schema['info']['title']}")
    print(f"  API 版本: {schema['info']['version']}")
    print("  ✅ OpenAPI Schema 正常")


if __name__ == "__main__":
    print("=" * 60)
    print("FastAPI 基础功能测试")
    print("=" * 60)

    try:
        test_root()
        test_health_check()
        test_docs()
        test_openapi()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
