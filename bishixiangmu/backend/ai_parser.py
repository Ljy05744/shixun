"""
AI自然语言解析器
支持模拟模式和真实API模式
新增：AI优先级推荐功能
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class AITaskParser:
    """AI任务解析器类"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.use_real_api = bool(self.api_key)

        if not self.use_real_api:
            print("🤖 AI解析器: 使用模拟模式（无需API密钥）")
        else:
            print("🤖 AI解析器: 使用API模式")

    def parse(self, text: str) -> Dict[str, Any]:
        """解析自然语言文本为任务数据"""
        if self.use_real_api and self.api_key:
            return self._parse_with_api(text)
        else:
            return self._parse_with_rules(text)

    def _parse_with_rules(self, text: str) -> Dict[str, Any]:
        """使用规则解析（模拟模式）"""
        # 提取标题（取前40个字符）
        title = text[:40].strip()
        if len(text) > 40:
            title += "..."

        # 初始化结果
        result = {
            "title": title,
            "description": f"从文本解析: {text}",
            "status": "pending",
            "priority": 3,
            "due_date": None
        }

        # 解析日期关键词
        date_keywords = {
            "今天": 0,
            "明天": 1,
            "后天": 2,
            "大后天": 3,
            "下周": 7,
            "下下周": 14,
            "下个月": 30
        }

        today = datetime.now().date()
        for keyword, days in date_keywords.items():
            if keyword in text:
                result["due_date"] = (today + timedelta(days=days)).isoformat()
                break

        # 解析时间点
        time_pattern = r'(\d{1,2})[:点](\d{0,2})?'
        time_match = re.search(time_pattern, text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            # 可以在描述中添加时间信息
            result["description"] += f"（时间: {hour:02d}:{minute:02d}）"

        # 解析优先级关键词
        priority_map = {
            "紧急": 1, "立刻": 1, "马上": 1, "尽快": 1, "高优先级": 1,
            "重要": 2, "优先": 2,
            "普通": 3, "一般": 3, "正常": 3,
            "不急": 4, "有空": 4, "低优先级": 4,
            "随便": 5, "任意": 5, "无限制": 5
        }

        for keyword, priority in priority_map.items():
            if keyword in text:
                result["priority"] = priority
                break

        # 解析状态关键词
        if "完成" in text or "做了" in text or "搞定" in text:
            result["status"] = "completed"
        elif "进行" in text or "正在" in text or "处理中" in text:
            result["status"] = "in_progress"

        # 使用AI推荐优先级
        result["priority"] = self.recommend_priority(result)

        return result

    def _parse_with_api(self, text: str) -> Dict[str, Any]:
        """使用真实API解析（这里用模拟替代）"""
        # 实际项目中可以调用 OpenAI/DeepSeek API
        # 这里为了简化，返回规则解析的结果

        base_result = self._parse_with_rules(text)

        if self.api_key and self.use_real_api:
            # 这里可以添加真实API调用代码
            print(f"📡 调用AI API分析: {text}")

            # 模拟AI更智能的分析
            base_result["ai_analyzed"] = True

            # 如果有真实API，可以在这里调用
            # 例如：response = requests.post(api_url, ...)
            # base_result.update(process_api_response(response))

            # 当前使用模拟数据
            import random
            # AI可以根据语义理解调整优先级
            ai_adjustment = random.choice([-1, 0, 1])  # 模拟AI微调
            base_result["priority"] = max(1, min(5, base_result["priority"] + ai_adjustment))

            # AI可以提供更详细的理由
            base_result["ai_reason"] = self._generate_ai_reason(text, base_result)

        return base_result

    def recommend_priority(self, task_data: Dict[str, Any]) -> int:
        """
        基于规则/AI推荐优先级（1-5，1最高）

        算法规则：
        1. 根据截止日期紧迫性
        2. 根据任务状态
        3. 根据内容关键词
        4. 综合计算
        """
        priority_score = 3  # 默认优先级

        # 1. 根据截止日期紧迫性
        if task_data.get("due_date"):
            due_date_str = task_data["due_date"]
            if isinstance(due_date_str, str):
                try:
                    due_date = datetime.fromisoformat(due_date_str).date()
                    days_until_due = (due_date - datetime.now().date()).days

                    # 根据剩余天数调整优先级
                    if days_until_due < 0:  # 已过期
                        priority_score = 1
                    elif days_until_due == 0:  # 今天
                        priority_score = 1
                    elif days_until_due <= 2:  # 2天内
                        priority_score = 2
                    elif days_until_due <= 7:  # 一周内
                        priority_score = 3
                    elif days_until_due <= 30:  # 一个月内
                        priority_score = 4
                    else:  # 更久
                        priority_score = 5
                except Exception:
                    # 日期解析失败，使用默认值
                    pass

        # 2. 根据状态（进行中的任务优先级更高）
        status = task_data.get("status", "pending")
        if status == "in_progress":
            priority_score = max(1, priority_score - 1)  # 提升一级优先级

        # 3. 关键词分析
        title = task_data.get("title", "").lower()
        description = task_data.get("description", "").lower()
        full_text = f"{title} {description}"

        # 紧急关键词权重最高
        urgent_keywords = ["紧急", "立刻", "马上", "尽快", "必须", "今天", "立即", "重要会议", "deadline", "截止"]
        important_keywords = ["重要", "优先", "关键", "主要", "核心", "会议", "演示", "汇报"]
        low_priority_keywords = ["有空", "不急", "以后", "改天", "空闲", "随意", "随便"]

        # 检查紧急关键词
        urgent_found = False
        for keyword in urgent_keywords:
            if keyword in full_text:
                priority_score = 1
                urgent_found = True
                break

        # 如果未找到紧急关键词，检查重要关键词
        if not urgent_found and priority_score > 2:
            for keyword in important_keywords:
                if keyword in full_text:
                    priority_score = min(2, priority_score)
                    break

        # 检查低优先级关键词
        for keyword in low_priority_keywords:
            if keyword in full_text and priority_score > 3:
                priority_score = min(5, priority_score + 1)  # 降低优先级
                break

        # 4. 确保优先级在有效范围内
        return max(1, min(5, priority_score))

    def _generate_ai_reason(self, text: str, task_data: Dict[str, Any]) -> str:
        """生成AI推荐理由"""
        reasons = []

        if task_data.get("due_date"):
            try:
                due_date = datetime.fromisoformat(task_data["due_date"]).date()
                days_until_due = (due_date - datetime.now().date()).days

                if days_until_due < 0:
                    reasons.append("任务已过期，需要立即处理")
                elif days_until_due <= 2:
                    reasons.append(f"截止日期仅剩{days_until_due}天")
                elif days_until_due <= 7:
                    reasons.append("截止日期在一周内")
            except:
                pass

        # 检查关键词
        full_text = f"{text} {task_data.get('title', '')} {task_data.get('description', '')}"
        full_text = full_text.lower()

        if any(word in full_text for word in ["紧急", "立刻", "马上", "尽快"]):
            reasons.append("检测到紧急关键词")
        elif any(word in full_text for word in ["重要", "优先", "关键"]):
            reasons.append("检测到重要关键词")
        elif any(word in full_text for word in ["有空", "不急", "以后"]):
            reasons.append("检测到低优先级关键词")

        if task_data.get("status") == "in_progress":
            reasons.append("任务正在进行中")

        # 如果没有特定理由，使用通用理由
        if not reasons:
            priority = task_data.get("priority", 3)
            reason_map = {
                1: "基于内容和时间分析，建议立即处理",
                2: "任务相对重要，建议优先安排",
                3: "任务正常，可按计划处理",
                4: "任务不急，可以稍后处理",
                5: "任务无时间限制，空闲时处理"
            }
            reasons.append(reason_map.get(priority, "基于AI分析推荐"))

        return "；".join(reasons)

    def validate_task_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和清理任务数据"""
        # 确保必要字段
        if not data.get("title"):
            data["title"] = "未命名任务"

        # 确保优先级在1-5之间
        priority = data.get("priority", 3)
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            data["priority"] = 3

        # 确保状态有效
        valid_statuses = ["pending", "in_progress", "completed"]
        if data.get("status") not in valid_statuses:
            data["status"] = "pending"

        # 清理描述
        if data.get("description") and len(data["description"]) > 1000:
            data["description"] = data["description"][:1000] + "..."

        return data

    def analyze_task_importance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        深入分析任务重要性（可选功能）
        返回更详细的分析结果
        """
        analysis = {
            "priority": task_data.get("priority", 3),
            "urgency": "medium",  # low, medium, high, critical
            "importance": "medium",  # low, medium, high
            "estimated_time": None,  # 预估耗时（分钟）
            "dependencies": [],  # 依赖关系
            "recommended_time": None  # 推荐处理时间
        }

        # 分析紧急性
        urgency = "medium"
        if task_data.get("due_date"):
            try:
                due_date = datetime.fromisoformat(task_data["due_date"]).date()
                days_until_due = (due_date - datetime.now().date()).days

                if days_until_due < 0:
                    urgency = "critical"
                elif days_until_due <= 1:
                    urgency = "high"
                elif days_until_due <= 3:
                    urgency = "medium"
                else:
                    urgency = "low"
            except:
                pass

        analysis["urgency"] = urgency

        # 分析重要性（基于关键词和内容）
        full_text = f"{task_data.get('title', '')} {task_data.get('description', '')}".lower()

        importance_keywords = {
            "critical": ["关键", "核心", "必须", "紧急", "重要会议", "deadline"],
            "high": ["重要", "优先", "主要", "会议", "演示", "汇报"],
            "medium": ["常规", "普通", "一般", "日常"],
            "low": ["有空", "不急", "随意", "休闲", "娱乐"]
        }

        importance = "medium"
        for level, keywords in importance_keywords.items():
            for keyword in keywords:
                if keyword in full_text:
                    importance = level
                    break
            if importance != "medium":
                break

        analysis["importance"] = importance

        # 根据紧急性、重要性和优先级综合评估
        if urgency == "critical" or importance == "critical":
            analysis["priority"] = 1
        elif urgency == "high" or importance == "high":
            analysis["priority"] = min(2, analysis["priority"])
        elif urgency == "low" and importance == "low":
            analysis["priority"] = max(4, analysis["priority"])

        return analysis


# 示例使用代码
if __name__ == "__main__":
    # 测试解析器
    parser = AITaskParser()

    test_cases = [
        "明天下午3点开会讨论项目进度，这个任务很重要",
        "有空的时候整理一下文件",
        "紧急！今天必须完成报告提交",
        "下周整理会议记录"
    ]

    for test_text in test_cases:
        print(f"\n📝 测试文本: {test_text}")
        result = parser.parse(test_text)
        print(f"📊 解析结果: {result}")

        # 测试优先级推荐
        recommended = parser.recommend_priority(result)
        print(f"🎯 AI推荐优先级: {recommended}")

        # 测试深入分析
        analysis = parser.analyze_task_importance(result)
        print(f"🔍 重要性分析: {analysis}")