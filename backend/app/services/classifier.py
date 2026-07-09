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
    ),
    Category.FOOD.value: ("recipe", "meal", "snack", "noodle", "salad", "coffee", "lunch"),
    Category.TRAVEL.value: ("itinerary", "hotel", "travel", "weekend", "train", "airport"),
}


SUBCATEGORY_HINTS: dict[str, tuple[str, str]] = {
    "Beauty": ("SPF and base makeup", "beauty"),
    "Fashion": ("Capsule styling", "fashion"),
    "Fitness": ("Short routine", "fitness"),
    "Work": ("Productivity system", "work"),
    "Study": ("Learning workflow", "study"),
    "Life": ("Home routine", "life"),
    "Food": ("Easy meal", "food"),
    "Travel": ("Trip planning", "travel"),
    "Other": ("General reference", "other"),
}


def classify_text(title: str, raw_text: str | None = None, ocr_text: str | None = None) -> tuple[str, str]:
    haystack = " ".join(part for part in [title, raw_text or "", ocr_text or ""] if part).lower()
    best_category = Category.OTHER.value
    best_score = 0

    for category, keywords in KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category, SUBCATEGORY_HINTS[best_category][0]
