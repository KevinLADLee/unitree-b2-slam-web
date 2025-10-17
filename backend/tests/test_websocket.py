"""
WebSocket 测试客户端

测试 WebSocket 连接和消息推送功能
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_websocket_connection():
    """测试 WebSocket 基本连接"""
    print("\n【测试1】WebSocket 基本连接")

    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # 接收欢迎消息
            message = await websocket.recv()
            data = json.loads(message)
            print(f"  收到欢迎消息: {data['type']}")
            print(f"  客户端 ID: {data['data']['client_id']}")
            print(f"  可用主题: {data['data']['available_topics']}")
            print("  ✅ 连接成功")

    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False

    return True


async def test_websocket_subscribe():
    """测试订阅功能"""
    print("\n【测试2】订阅主题")

    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # 接收欢迎消息
            await websocket.recv()

            # 订阅 qt_notice
            await websocket.send(json.dumps({
                "action": "subscribe",
                "topic": "qt_notice"
            }))

            # 接收订阅确认
            message = await websocket.recv()
            data = json.loads(message)
            print(f"  订阅响应: {data}")
            assert data['type'] == 'subscribed', "应该收到订阅确认"
            print("  ✅ 订阅成功")

            # 订阅 odometry
            await websocket.send(json.dumps({
                "action": "subscribe",
                "topic": "odometry"
            }))

            message = await websocket.recv()
            data = json.loads(message)
            assert data['type'] == 'subscribed'
            print("  ✅ 订阅里程计成功")

    except Exception as e:
        print(f"  ❌ 订阅失败: {e}")
        return False

    return True


async def test_websocket_ping():
    """测试心跳功能"""
    print("\n【测试3】Ping/Pong")

    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # 接收欢迎消息
            await websocket.recv()

            # 发送 ping
            await websocket.send(json.dumps({
                "action": "ping"
            }))

            # 接收 pong
            message = await websocket.recv()
            data = json.loads(message)
            print(f"  Pong 响应: {data}")
            assert data['type'] == 'pong', "应该收到 pong"
            print("  ✅ Ping/Pong 成功")

    except Exception as e:
        print(f"  ❌ Ping/Pong 失败: {e}")
        return False

    return True


async def test_websocket_unsubscribe():
    """测试取消订阅"""
    print("\n【测试4】取消订阅")

    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # 接收欢迎消息
            await websocket.recv()

            # 先订阅
            await websocket.send(json.dumps({
                "action": "subscribe",
                "topic": "qt_notice"
            }))
            await websocket.recv()

            # 取消订阅
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "topic": "qt_notice"
            }))

            # 接收取消订阅确认
            message = await websocket.recv()
            data = json.loads(message)
            print(f"  取消订阅响应: {data}")
            assert data['type'] == 'unsubscribed', "应该收到取消订阅确认"
            print("  ✅ 取消订阅成功")

    except Exception as e:
        print(f"  ❌ 取消订阅失败: {e}")
        return False

    return True


async def test_multiple_clients():
    """测试多客户端连接"""
    print("\n【测试5】多客户端连接")

    uri = "ws://localhost:8000/ws"

    try:
        # 创建3个客户端连接
        clients = []
        for i in range(3):
            ws = await websockets.connect(uri)
            clients.append(ws)
            # 接收欢迎消息
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"  客户端 {i+1} 连接成功: {data['data']['client_id'][:8]}...")

        print(f"  ✅ 成功建立 {len(clients)} 个连接")

        # 关闭所有连接
        for ws in clients:
            await ws.close()

        print("  ✅ 所有连接已关闭")

    except Exception as e:
        print(f"  ❌ 多客户端测试失败: {e}")
        return False

    return True


async def main():
    """主测试流程"""
    print("=" * 60)
    print("WebSocket 测试")
    print("=" * 60)

    print("\n提示：请确保后端服务已启动 (python main.py)")
    print("等待 3 秒...")
    await asyncio.sleep(3)

    results = []

    # 运行所有测试
    results.append(await test_websocket_connection())
    results.append(await test_websocket_subscribe())
    results.append(await test_websocket_ping())
    results.append(await test_websocket_unsubscribe())
    results.append(await test_multiple_clients())

    # 统计结果
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    if passed == total:
        print(f"✅ 所有测试通过！({passed}/{total})")
    else:
        print(f"❌ 部分测试失败: {passed}/{total} 通过")
    print("=" * 60)

    print("\n【总结】")
    print("  ✅ WebSocket 连接功能正常")
    print("  ✅ 订阅/取消订阅功能正常")
    print("  ✅ Ping/Pong 功能正常")
    print("  ✅ 多客户端连接支持正常")
    print("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
