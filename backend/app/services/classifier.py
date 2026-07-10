from __future__ import annotations

from app.models import Category


ALLOWED_CATEGORIES = [category.value for category in Category]


KEYWORDS: dict[str, tuple[str, ...]] = {
    Category.BEAUTY.value: (
        "spf",
        "sunscreen",
        "base",
        "foundation",
        "serum",
        "lip",
        "skin",
        "makeup",
        "concealer",
        "妆",
        "护肤",
        "口红",
        "粉底",
        "美妆",
        "美女感",
        "化妆",
        "防晒",
        "发型",
        "美甲",
        "穿孔护理",
    ),
    Category.FASHION.value: (
        "outfit",
        "capsule",
        "jacket",
        "wardrobe",
        "linen",
        "shoes",
        "bag",
        "denim",
        "穿搭",
        "ootd",
        "衣服",
        "钩织",
        "棒织",
        "包",
        "鞋",
        "配饰",
        "钩针",
        "编织",
        "披肩",
        "毛衣",
    ),
    Category.FITNESS.value: (
        "mobility",
        "workout",
        "pilates",
        "strength",
        "stretch",
        "protein",
        "run",
        "fitness",
        "健身",
        "训练",
        "减脂",
        "饮食",
        "体态",
        "瑜伽",
        "普拉提",
        "跑步",
    ),
    Category.WORK.value: (
        "meeting",
        "notion",
        "calendar",
        "workflow",
        "presentation",
        "focus",
        "email",
        "work",
        "面试",
        "职业",
        "工作",
        "转行",
        "ai engineer",
        "简历",
        "求职",
        "behavior",
        "公司",
        "工作流",
        "职场",
    ),
    Category.STUDY.value: (
        "study",
        "anki",
        "language",
        "exam",
        "reading",
        "notes",
        "flashcard",
        "paper",
        "学习",
        "leetcode",
        "research",
        "科研",
        "claude code",
        "codex",
        "论文",
        "虚拟细胞",
        "virtual-cell",
        "aivc",
        "ai memory",
        "agent",
        "源码",
        "黑客松",
        "比赛",
        "公共卫生",
    ),
    Category.LIFE.value: (
        "routine",
        "home",
        "cleaning",
        "habit",
        "morning",
        "budget",
        "organize",
        "desk",
        "情绪",
        "生活",
        "恋爱",
        "家居",
        "记录",
    ),
    Category.FOOD.value: (
        "recipe",
        "meal",
        "snack",
        "noodle",
        "salad",
        "coffee",
        "lunch",
        "美食",
        "餐厅",
        "吃",
        "菜",
        "饮品",
        "鸡尾酒",
        "吃喝",
        "下酒菜",
        "菜谱",
    ),
    Category.TRAVEL.value: (
        "itinerary",
        "hotel",
        "travel",
        "weekend",
        "train",
        "airport",
        "旅行",
        "邮轮",
        "城市",
        "攻略",
        "海岛",
    ),
}


def classify_text(
    title: str,
    raw_text: str | None = None,
    ocr_text: str | None = None,
) -> tuple[str, str | None]:
    """Classify quickly from the saved-post title only.

    Body text and OCR are intentionally ignored because they are unavailable or
    unreliable for many video posts.
    """
    del raw_text, ocr_text
    haystack = (title or "").strip().lower()
    best_category = Category.UNCATEGORIZED.value
    best_score = 0

    for category, keywords in KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category, None
