// Built-in category catalog for the deterministic keyword classifier.
// Ported from backend/app/category_presets.py — keep the two in sync.
// Each preset's `slug` is the canonical value stored on a post's category.

export const UNCATEGORIZED_SLUG = "Uncategorized";
export const UNCATEGORIZED = { slug: UNCATEGORIZED_SLUG, label_zh: "未分类", label_en: "Uncategorized" };

export const CATEGORY_PRESETS = [
  { slug: "Beauty", label_zh: "美妆", label_en: "Beauty", keywords: ["护肤", "口红", "粉底", "美妆", "防晒", "精华", "面膜", "化妆", "妆", "美甲", "发型", "美女感", "穿孔护理", "skincare", "makeup", "serum", "spf", "sunscreen", "foundation", "concealer", "lip"] },
  { slug: "Fashion", label_zh: "穿搭", label_en: "Fashion", keywords: ["穿搭", "搭配", "衣服", "包包", "鞋", "配饰", "牛仔", "outfit", "ootd", "wardrobe", "capsule", "jacket", "linen", "denim", "shoes", "bag"] },
  { slug: "Handcraft", label_zh: "手工", label_en: "Handcraft", keywords: ["钩针", "钩织", "针织", "编织", "棒针", "棒织", "披肩", "毛衣", "拼豆", "粘土", "手工", "手作", "diy", "crochet", "knit", "knitting", "embroidery"] },
  { slug: "Fitness", label_zh: "健身", label_en: "Fitness", keywords: ["健身", "减脂", "增肌", "训练", "瑜伽", "普拉提", "跑步", "体态", "拉伸", "workout", "pilates", "strength", "stretch", "mobility", "protein", "fitness"] },
  { slug: "Food", label_zh: "美食", label_en: "Food", keywords: ["美食", "菜谱", "食谱", "探店", "烘焙", "下厨", "餐厅", "吃", "菜", "饮品", "鸡尾酒", "下酒菜", "咖啡", "recipe", "meal", "snack", "noodle", "salad", "coffee", "lunch"] },
  { slug: "Study", label_zh: "学习", label_en: "Study", keywords: ["学习", "考研", "考试", "论文", "笔记", "雅思", "英语", "科研", "研究", "源码", "黑客松", "比赛", "公共卫生", "虚拟细胞", "study", "exam", "leetcode", "paper", "research", "anki", "flashcard", "claude code", "codex", "virtual-cell", "aivc", "ai memory", "agent"] },
  { slug: "Work", label_zh: "职场", label_en: "Work", keywords: ["面试", "简历", "求职", "职场", "职业", "工作", "转行", "副业", "公司", "工作流", "resume", "interview", "meeting", "notion", "workflow", "presentation", "ai engineer"] },
  { slug: "Life", label_zh: "生活", label_en: "Life", keywords: ["生活", "日常", "vlog", "好物", "记录", "习惯", "早八", "早起", "routine", "habit", "morning", "cleaning", "organize"] },
  { slug: "Travel", label_zh: "旅行", label_en: "Travel", keywords: ["旅行", "旅游", "攻略", "邮轮", "海岛", "城市", "citywalk", "自驾", "酒店", "机票", "travel", "itinerary", "hotel", "weekend", "airport"] },
  { slug: "Home", label_zh: "家居", label_en: "Home", keywords: ["家居", "装修", "收纳", "租房", "布置", "改造", "宜家", "家装", "home", "interior", "ikea", "desk"] },
  { slug: "Tech", label_zh: "数码", label_en: "Tech", keywords: ["数码", "手机", "电脑", "相机", "耳机", "平板", "键盘", "充电", "iphone", "macbook", "ipad", "gadget", "tech"] },
  { slug: "Parenting", label_zh: "母婴", label_en: "Parenting", keywords: ["母婴", "宝宝", "育儿", "辅食", "孕期", "亲子", "带娃", "baby", "parenting", "toddler"] },
  { slug: "Pets", label_zh: "宠物", label_en: "Pets", keywords: ["宠物", "养猫", "养狗", "猫", "狗", "主子", "猫咪", "狗狗", "cat", "dog", "pet", "puppy", "kitten"] },
  { slug: "Cars", label_zh: "汽车", label_en: "Cars", keywords: ["汽车", "试驾", "提车", "新能源", "油耗", "改装车", "car", "tesla", "byd", "ev"] },
  { slug: "Photography", label_zh: "摄影", label_en: "Photography", keywords: ["摄影", "拍照", "构图", "修图", "人像", "出片", "运镜", "photography", "lightroom", "pose", "photo"] },
  { slug: "Finance", label_zh: "理财", label_en: "Finance", keywords: ["理财", "基金", "股票", "存钱", "记账", "投资", "省钱", "finance", "budget", "invest", "saving"] },
  { slug: "Reading", label_zh: "读书", label_en: "Reading", keywords: ["读书", "书单", "阅读", "书评", "好书", "book", "reading", "bookshelf"] },
  { slug: "Design", label_zh: "设计", label_en: "Design", keywords: ["设计", "插画", "绘画", "平面", "排版", "配色", "design", "illustration", "figma", "ui", "ux"] },
  { slug: "Wellness", label_zh: "养生", label_en: "Wellness", keywords: ["养生", "睡眠", "冥想", "情绪", "中医", "健康", "泡脚", "心理", "wellness", "sleep", "mental", "meditation"] },
  { slug: "Relationship", label_zh: "情感", label_en: "Relationship", keywords: ["恋爱", "情感", "分手", "亲密关系", "脱单", "暗恋", "相处", "relationship", "dating", "couple"] },
  { slug: "Gaming", label_zh: "游戏", label_en: "Gaming", keywords: ["游戏", "原神", "手游", "端游", "攻略图", "game", "steam", "switch", "gaming"] },
  { slug: "Wedding", label_zh: "婚礼", label_en: "Wedding", keywords: ["婚礼", "婚纱", "备婚", "结婚", "求婚", "婚戒", "wedding", "bride"] },
  { slug: "Music", label_zh: "音乐", label_en: "Music", keywords: ["音乐", "吉他", "钢琴", "唱歌", "乐器", "编曲", "music", "guitar", "piano"] },
];

export const PRESET_BY_SLUG = Object.fromEntries(CATEGORY_PRESETS.map((p) => [p.slug, p]));
export const ALL_PRESET_SLUGS = CATEGORY_PRESETS.map((p) => p.slug);
