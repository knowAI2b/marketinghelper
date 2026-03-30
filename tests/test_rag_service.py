#!/usr/bin/env python3
"""RAG 服务测试脚本。

测试 RAG 客户端与 xhs_agent API 的交互。
API 端点:
- GET  /healthz - 健康检查
- POST /v1/topic-cards/jobs - 创建任务
- GET  /v1/topic-cards/jobs/{job_id} - 获取任务状态
- GET  /v1/topic-cards/{job_id} - 获取选题卡结果
"""
import os
import sys

# 设置测试环境变量
os.environ["RAG_SERVICE_URL"] = "http://192.168.1.27:3001"
os.environ["RAG_ENABLED"] = "true"
os.environ["RAG_TIMEOUT"] = "180"

# 清除模块缓存
for mod in list(sys.modules.keys()):
    if 'xhs_assistant' in mod:
        del sys.modules[mod]

from dotenv import load_dotenv
load_dotenv()

from xhs_assistant.services.rag import RagClient, get_rag_client
from xhs_assistant.shared.config import config


def test_health_check():
    """测试健康检查"""
    print("\n" + "=" * 60)
    print("测试 1: 健康检查 (GET /healthz)")
    print("=" * 60)

    client = RagClient(base_url="http://192.168.1.27:3001")
    print(f"服务地址: {client._base_url}")
    print(f"RAG 启用: {config.rag.enabled}")

    healthy = client.health_check()
    print(f"健康检查结果: {healthy}")

    return healthy


def test_create_job():
    """测试创建任务"""
    print("\n" + "=" * 60)
    print("测试 2: 创建任务 (POST /v1/topic-cards/jobs)")
    print("=" * 60)

    client = RagClient(base_url="http://192.168.1.27:3001")

    try:
        job_id = client.create_topic_card_job(
            product="咖啡",
            category="饮品",
            topic="春季新品",
            campaign="拉新种草",
        )
        print(f"✓ 任务创建成功!")
        print(f"  job_id: {job_id}")
        return job_id
    except Exception as e:
        print(f"✗ 任务创建失败: {e}")
        return None


def test_get_status(job_id: str):
    """测试获取任务状态"""
    print("\n" + "=" * 60)
    print("测试 3: 获取任务状态 (GET /v1/topic-cards/jobs/{job_id})")
    print("=" * 60)

    client = RagClient(base_url="http://192.168.1.27:3001")

    try:
        status = client.get_job_status(job_id)
        print(f"任务状态: {status.get('status', 'unknown')}")
        print(f"进度: {status.get('progress', {})}")
        return status
    except Exception as e:
        print(f"获取状态失败: {e}")
        return None


def test_full_workflow():
    """测试完整流程"""
    print("\n" + "=" * 60)
    print("测试 4: 完整工作流")
    print("=" * 60)

    client = RagClient(
        base_url="http://192.168.1.27:3001",
        timeout=300,  # 5分钟超时
    )

    if not client.is_available():
        print("服务不可用，跳过测试")
        return None

    try:
        print("开始获取选题卡（可能需要几分钟）...")
        result = client.get_topic_card_for_product(
            product="咖啡",
            category="饮品",
            topic="春季新品",
            use_cache=False,
        )

        print(f"\n结果状态: {result.status}")
        print(f"Job ID: {result.job_id}")

        if result.is_success() and result.topic_card:
            tc = result.topic_card
            print(f"\n=== 选题卡数据 ===")
            print(f"趋势摘要: {tc.trend_summary[:100] if tc.trend_summary else '无'}...")
            print(f"热门标题: {tc.title_hooks[:5] if tc.title_hooks else '无'}")
            print(f"推荐标签: {tc.recommended_tags[:10] if tc.recommended_tags else '无'}")
            print(f"用户问题: {tc.faq_top_questions[:3] if tc.faq_top_questions else '无'}")
            print(f"合规风险: {tc.compliance_risks[:3] if tc.compliance_risks else '无'}")
        else:
            print(f"错误: {result.error}")

        return result

    except Exception as e:
        print(f"工作流失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 60)
    print("RAG 服务测试")
    print("=" * 60)
    print(f"测试地址: http://192.168.1.27:3001")
    print()

    # 测试 1: 健康检查
    healthy = test_health_check()

    if not healthy:
        print("\n⚠ 服务健康检查失败，可能原因：")
        print("  1. 服务未启动")
        print("  2. 端口不正确（默认 3001）")
        print("  3. 网络不可达")
        print("\n请检查服务状态: cd /path/to/xhs_agent && npm start")
        print("\n继续尝试其他测试...")

    # 测试 2: 创建任务
    job_id = test_create_job()
    if job_id:
        # 测试 3: 获取状态
        test_get_status(job_id)

    # 测试 4: 完整工作流
    test_full_workflow()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()