from app.models import Category
from app.services.ai_mock import MockAIProvider


def test_mock_ai_classifies_from_title_without_summary():
    result = MockAIProvider().summarize_and_classify(
        {
            "title": "把Codex和Claude配成科研助手",
            "raw_text": "这篇笔记介绍如何把 Codex 和 Claude Code 配成科研助手。它强调用工具整理论文、生成实验计划，并把结果沉淀成可复用模板。",
            "ocr_text": "",
        }
    )

    assert result.ai_summary is None
    assert result.category == Category.STUDY.value
    assert result.key_points == []


def test_mock_ai_classifies_short_title():
    result = MockAIProvider().summarize_and_classify(
        {"title": "夏季钩织背心", "raw_text": "夏季钩织背心", "ocr_text": ""}
    )

    assert result.ai_summary is None
    # Knitting keywords now live in the dedicated Handcraft category.
    assert result.category == "Handcraft"


def test_mock_ai_category_falls_back_to_uncategorized():
    result = MockAIProvider().summarize_and_classify(
        {"title": "一条暂时看不出主题的收藏", "raw_text": "没有明显分类关键词的简短素材。", "ocr_text": ""}
    )

    assert result.category == Category.UNCATEGORIZED.value
    assert result.ai_summary is None


def test_mock_ai_keyword_categories():
    provider = MockAIProvider()

    assert provider.summarize_and_classify({"title": "面试准备", "raw_text": "无关正文", "ocr_text": ""}).category == Category.WORK.value
    assert provider.summarize_and_classify({"title": "贵阳美食", "raw_text": "无关正文", "ocr_text": ""}).category == Category.FOOD.value
    assert provider.summarize_and_classify({"title": "邮轮旅行攻略", "raw_text": "穿搭", "ocr_text": ""}).category == Category.TRAVEL.value


def test_mock_ai_ignores_body_text_for_classification():
    result = MockAIProvider().summarize_and_classify(
        {"title": "一条暂时看不出主题的收藏", "raw_text": "面试 简历 求职", "ocr_text": "美食"}
    )

    assert result.category == Category.UNCATEGORIZED.value


def test_mock_ai_classifies_research_titles_before_generic_travel_hints():
    provider = MockAIProvider()

    assert provider.summarize_and_classify({"title": "Awesome-Virtual-Cell 大更新"}).category == Category.STUDY.value
    assert provider.summarize_and_classify({"title": "公共卫生专业如何上AI这艘快船 攻略版"}).category == Category.STUDY.value
