# -*- coding: utf-8 -*-
"""
build_final_stages.py
Build and validate complete world stages for Mushoku Tensei Volumes 1 to 15.
Generates:
- shared_world.json (26 universal entries)
- stage1_childhood.json (16 entries, Vols 1-2)
- stage2_demon_continent.json (36 entries, Vols 3-6)
- stage3_academy.json (31 entries, Vols 7-11)
- stage4_labyrinth_family.json (24 entries, Vols 12-13)
- stage5_dragon_god.json (25 entries, Vols 14-15)
- world_summary.md (comprehensive human-readable overview)
"""

import os
import json
import re

STAGE1_FILE = "world_stages/stage1_childhood.json"
STAGE2_FILE = "world_stages/stage2_demon_continent.json"
STAGE3_FILE = "world_stages/stage3_academy.json"
SHARED_FILE = "world_stages/shared_world.json"

STAGE4_FILE = "world_stages/stage4_labyrinth_family.json"
STAGE5_FILE = "world_stages/stage5_dragon_god.json"
SUMMARY_FILE = "world_stages/world_summary.md"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def char_count(s):
    # Count Chinese characters, punctuation, letters and numbers in content
    return len(re.sub(r'\s+', '', s))

def validate_entries(entries, name):
    print(f"[{name}] Validating {len(entries)} entries...")
    core_cnt = 0
    sec_cnt = 0
    for i, e in enumerate(entries):
        # Check required fields
        required = ["keywords", "content", "timeline", "priority", "category", "reveal_arc", "spoiler", "source_chapters", "note"]
        for r in required:
            if r not in e:
                raise ValueError(f"Entry {i} in {name} missing field {r}: {e}")
        
        c = e["content"]
        cl = char_count(c)
        if cl < 50 or cl > 150:
            raise ValueError(f"Entry {i} ({e['keywords'][0]}) in {name} length {cl} not in 50-150: '{c}'")
        
        if e["priority"] == "核心":
            core_cnt += 1
        elif e["priority"] == "次要":
            sec_cnt += 1
        else:
            raise ValueError(f"Invalid priority '{e['priority']}' in {name}: {e}")
    print(f"[{name}] Total: {len(entries)}, Core: {core_cnt}, Secondary: {sec_cnt} - VALIDATION PASSED!")

# Load existing validated shared, stage1, stage2, stage3
shared_entries = load_json(SHARED_FILE)
stage1_entries = load_json(STAGE1_FILE)
stage2_entries = load_json(STAGE2_FILE)
stage3_entries = load_json(STAGE3_FILE)

# Enrich shared_world with new universal concepts discovered in Vols 12-15
new_shared = [
    {
        "keywords": ["六面世界与无之世界", "六面世界", "无之世界", "太古六界"],
        "content": "太古创世神话格局。世界原本由六个相互连接的独立世界（人界、魔界、龙界、兽界、天界、海界）构成，环绕着中央的无之世界。太古大战导致其余五界碎裂崩塌，唯留人界与虚无的无之世界，人神即居于无之世界深处。",
        "timeline": "通用",
        "priority": "核心",
        "category": "力量体系",
        "reveal_arc": "第14卷后",
        "spoiler": True,
        "source_chapters": ["014_03", "014_10", "015_02"],
        "note": "老鲁迪日记与佩尔基乌斯太古壁画揭示的世界真相"
    },
    {
        "keywords": ["吸魔石", "吸收魔力魔石", "魔石特性", "抗魔质料"],
        "content": "具备吸收与无效化魔力特质的罕见魔石。多产自特定高位龙族魔物（如魔石九头龙）体内，能将接触到的魔力与法术直接吸收吞噬，使普通魔术完全无效。常被顶级工匠用于打造反魔铠甲、魔导假肢掌心或解咒抑制器。",
        "timeline": "通用",
        "priority": "核心",
        "category": "力量体系",
        "reveal_arc": "第12卷后",
        "spoiler": False,
        "source_chapters": ["012_08", "013_05", "014_07"],
        "note": "迷宫篇后广泛应用于魔导铠与义手"
    },
    {
        "keywords": ["神刀与名器魔剑", "神刀", "凤雅龙剑", "四十八把魔剑", "王龙王之剑"],
        "content": "世间登峰造极的名匠以神龙遗骨或王龙王残骸铸造的至高兵刃。包括初代龙神相传的神刀、绝世名匠龙皇为剑神打造的七剑（如无视防御的凤雅龙剑），以及王龙王骨头打造的四十八把魔剑。具有破除斗气与斩断法术之神异。",
        "timeline": "通用",
        "priority": "次要",
        "category": "物品",
        "reveal_arc": "第15卷后",
        "spoiler": False,
        "source_chapters": ["015_08", "015_09", "015_13"],
        "note": "列强与剑王级神兵利器"
    },
    {
        "keywords": ["异世界综合征与魔石病", "杜莱病", "干涸病", "魔石病", "魔力排泄障碍"],
        "content": "涉及魔力与肉体的极恶绝症。杜莱病（干涸病）系缺乏魔力免疫机制的异世界肉身穿越者因环境魔力滞留脏腑所致，需饮用魔大陆索卡司茶根治；魔石病则由特殊老鼠传染，令宿主内脏结晶化致死，唯神级解毒魔术方可化解。",
        "timeline": "通用",
        "priority": "次要",
        "category": "力量体系",
        "reveal_arc": "第14卷后",
        "spoiler": True,
        "source_chapters": ["014_04", "015_01", "015_06"],
        "note": "七星患病与未来日记中的致命危机"
    }
]

# Check existing keywords in shared to avoid duplicates
existing_shared_kw = set()
for e in shared_entries:
    existing_shared_kw.update(e["keywords"])

for ns in new_shared:
    if ns["keywords"][0] not in existing_shared_kw:
        shared_entries.append(ns)

# Stage 4: 转移迷宫救援与两妻家庭篇 (Vols 12-13, Ages 16-17)
stage4_entries = [
    {
        "keywords": ["鲁迪乌斯", "鲁迪", "泥沼", "两妻之夫"],
        "content": "十六至十七岁，经历转移迷宫激战斩杀魔石九头龙，救出母亲塞妮丝，但失去左手且父亲保罗阵亡，陷入重度自闭。在洛琪希抚慰下重整精神，纳洛琪希为第二位妻子，与希露菲和睦同居，长女露西诞生，装配装有吸魔石的义手。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_09", "012_11", "013_02", "013_07"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["洛琪希", "洛琪希·米格路德", "次席妻子", "水王级魔术师"],
        "content": "受困转移迷宫一个月濒死时被鲁迪乌斯救出并倾心；保罗牺牲后主动献身抚慰濒临崩溃的鲁迪。随鲁迪回到夏利亚获得正妻希露菲大度接纳，成为鲁迪第二位妻子，担任拉诺亚魔法大学水系教师并晋升水王级，不久怀上二胎。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_04", "012_11", "013_01", "013_06"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["希露菲叶特", "希露菲", "正妻希露菲", "菲兹"],
        "content": "鲁迪乌斯正妻，诞下长女露西·格雷拉特。为人贤良大度，深知洛琪希对鲁迪的启蒙之恩与迷宫拯救之功，主动以宽广胸怀接纳洛琪希作为侧室共同生活，化解多妻尴尬，情同姐妹，共同主持温馨和谐的大家庭。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_15", "013_02", "013_07", "013_08"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["塞妮丝", "塞妮丝·格雷拉特", "结晶中的母亲", "失智母亲"],
        "content": "鲁迪之母。自贝卡利特转移迷宫最深处的巨大魔力结晶中被解救。因长期充当迷宫动力核心，心智退化丧失记忆与语言能力，犹如纯洁幼儿，但在家中仍保留着对儿女无微不至的温柔母性反应，受爱夏悉心照料。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_10", "012_12", "013_04", "013_09"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["保罗", "保罗·格雷拉特", "殉职父亲", "黑狼剑士"],
        "content": "鲁迪之父，前黑狼之牙剑士。率队远征贝卡利特转移迷宫，在最深处与魔石九头龙的决死肉搏中，为替鲁迪乌斯抵挡致命践踏而被踩碎下半身壮烈牺牲。遗体火葬后安葬于夏利亚，成为鲁迪心中永远敬重的精神支柱。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_09", "012_10", "012_16"],
        "note": "第12卷牺牲"
    },
    {
        "keywords": ["艾莉娜丽洁", "艾莉娜丽洁·格利摩尔", "克里夫之妻", "长耳族老兵"],
        "content": "克里夫之妻。在转移迷宫中展现高超前卫战技与冷静指挥；保罗牺牲后以长辈阅历全力稳定队伍心智，撮合洛琪希与鲁迪；归乡后与克里夫感情甚笃，全力配合克里夫研发针对自身魔力诅咒的魔道具，展现贤妻风范。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_08", "012_11", "013_02", "013_07"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["基斯", "基斯·诺卡匹亚", "猴貌盗贼", "原黑狼斥候"],
        "content": "前黑狼之牙猴面盗贼。在转移迷宫探索中承担核心探路斥候重任，全力营救塞妮丝与洛琪希；保罗牺牲后协助妥善操办后事，于拉庞结算战利品分红后与鲁迪挥泪告别，继续独自浪迹天涯。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_03", "012_09", "012_12"],
        "note": "卷12后暂别"
    },
    {
        "keywords": ["塔尔韩多", "塔尔韩多·米尔哈斯", "矿坑族老战士", "大盾术师"],
        "content": "前黑狼之牙矿坑族魔术战士。身披重甲手持巨盾精通土火法术，在转移迷宫中誓死掩护队友抵御凶暴魔物；保罗牺牲后深受打击痛饮哀思，后与鲁迪告别返回北方矿坑族领地修养。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_03", "012_09", "012_12"],
        "note": "卷12后暂别"
    },
    {
        "keywords": ["诺伦", "诺伦·格雷拉特", "学生会骨干", "传记作者"],
        "content": "鲁迪亲妹，魔法大学学生会核心成员。惊闻保罗战死极其悲恸，起初对洛琪希以第二任妻子进门深感抗拒并激烈反对，后在艾莉娜丽洁开导与家庭温暖下释怀，决心提笔为保罗与瑞杰路德撰写真实传记。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_14", "013_03", "013_05"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["爱夏", "爱夏·格雷拉特", "天才总管", "家庭大管家"],
        "content": "鲁迪同父异母妹，格雷拉特家内管大总管。展现出神入化的家务与经商协调才能，全权料理大家庭杂务，悉心看护心智退化的塞妮丝与侄女露西，并协助鲁迪开展旱作水稻试验田与魔木盆景培育。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_14", "013_04", "013_09"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["克里夫", "克里夫·格利摩尔", "解咒魔术师", "教皇之孙"],
        "content": "艾莉娜丽洁之夫，米里斯天才魔术师。深入钻研魔道具与诅咒机理，利用九头龙体内的吸魔石为艾莉娜丽洁定制魔力吸收释放手环；对鲁迪多妻行为虽有信仰抵触，但深明大义并给予充分包容理解。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_15", "013_02", "013_05", "013_07"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["札诺巴", "札诺巴·西隆", "怪力义手创制者", "人形工匠"],
        "content": "西隆第三王子。迷宫战后与鲁迪废寝忘食研究狂龙王自动人偶内部精密核心，巧妙结合九头龙吸魔石，亲手为失去左臂的鲁迪打造出可自由抓握与吸魔的强力魔导义手（札里夫义手）。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_14", "013_02", "013_05"],
        "note": "卷12-13状态"
    },
    {
        "keywords": ["莎拉", "莎拉·金发弓手", "Amazones Ace", "释怀故人"],
        "content": "现加盟全女性S级冒险者队伍Amazones Ace的顶级弓手。在拉诺亚冬季偶然重逢鲁迪乌斯，双方平静交流，彻底解开当年罗森堡时期的情感心结与失言误会，见证鲁迪成家后真诚献上祝福并奔赴远方。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_10"],
        "note": "卷13心结化解"
    },
    {
        "keywords": ["艾莉丝", "艾莉丝·伯雷亚斯·格雷拉特", "狂剑王艾莉丝", "剑之圣地艾莉丝"],
        "content": "剑之圣地苦修的剑王，人称狂剑王。在剑神加尔与水神列妲共同磨砺下将剑神流与北神流精义浑然一体，压制妮娜与伊佐露缇，成为圣地最年轻强悍剑王，心无旁骛只为在未来的龙神威胁下守护鲁迪。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_13", "014_12"],
        "note": "剑之圣地闭关阶段"
    },
    {
        "keywords": ["迷宫都市拉庞", "拉庞", "贝西摩斯骨骸之城", "贝卡利特中心都市"],
        "content": "坐落于贝卡利特大陆大沙漠绿洲的迷宫枢纽城市。依托上古巨兽贝西摩斯巨大骨骸与周边转移迷宫而建，商贩云集，聚集着大量S级冒险者，以魔力附加品、魔石开采交易与高风险迷宫悬赏为核心经济命脉。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "地理",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_01", "012_02", "012_13"],
        "note": "卷12核心舞台"
    },
    {
        "keywords": ["贝卡利特转移迷宫", "转移迷宫", "六层转移迷宫", "九头龙之巢"],
        "content": "位于贝卡利特大陆近郊的极恶S级古代六层迷宫。迷宫内部充斥着无数极具迷惑性且错综复杂的空间转移魔法阵陷阱，魔物等级极高，最底层为魔石九头龙驻守的灰色宫殿，曾囚禁洛琪希并封印塞妮丝。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "地理",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_03", "012_07", "012_08"],
        "note": "卷12核心迷宫"
    },
    {
        "keywords": ["魔石九头龙", "魔石多头龙", "迷宫守护者", "恶魔之龙"],
        "content": "贝卡利特转移迷宫最深处的守护巨兽。浑身覆盖能吸收全系魔术的深绿魔石鳞片，具九颗头颅与惊人自愈再生力。常规魔术对其完全无效，唯有用物理重斩断首并施以火魔术灼烧创面坏死方能彻底击灭。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "种族",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_08", "012_09"],
        "note": "卷12关底守护者"
    },
    {
        "keywords": ["转移迷宫决战与保罗殉职", "转移迷宫决战", "保罗战死", "塞妮丝获救"],
        "content": "甲龙历422年，保罗搜救团联合鲁迪深入转移迷宫最深处的死斗。虽成功斩杀魔石九头龙救出塞妮丝，但保罗为救鲁迪被踩断下身牺牲，鲁迪失去左前臂，塞妮丝丧失心智，成为全书最为惨烈的惨胜。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "历史",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["012_09", "012_10", "012_11"],
        "note": "第12卷核心转折事件"
    },
    {
        "keywords": ["露西·格雷拉特诞生", "露西诞生", "长女降生", "露西·格雷拉特"],
        "content": "甲龙历423年，鲁迪乌斯与希露菲叶特的长女露西在夏利亚宅邸平安诞生。作为格雷拉特家族灾后新生的象征，其降生极大驱散了保罗阵亡的家族阴霾，标志着鲁迪乌斯正式步入成熟为父的人生轨道。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "历史",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_02", "013_04"],
        "note": "卷13标志性家族事件"
    },
    {
        "keywords": ["札里夫义手", "魔导义手", "吸魔石义手", "鲁迪左手义肢"],
        "content": "札诺巴利用狂龙王卡奥斯自动人偶核心机构与魔石九头龙吸魔石为鲁迪断臂特制的魔导假肢。外观呈哑光金属，掌心机关可自由开闭释放吸魔力场吞噬魔法，并提供强劲握力与自保功能。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "物品",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_02", "013_05"],
        "note": "鲁迪断臂后的主力装备"
    },
    {
        "keywords": ["水王级魔术「雷光」", "雷光", "水王级魔术", "落雷压缩魔术"],
        "content": "水王级高阶攻击魔术。以水圣级「豪雷积雨云」制造高空饱和雷云为前置，强行引导压缩天雷形成毁灭性落雷打击，消耗极大。洛琪希在夏利亚郊外倾囊传授鲁迪，后被鲁迪改良为无咏唱版与麻痹电击技。",
        "timeline": "迷宫与两妻篇",
        "priority": "核心",
        "category": "力量体系",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_06"],
        "note": "洛琪希亲授鲁迪王级攻击术"
    },
    {
        "keywords": ["魔物与魔兽人工驯化法则", "魔木比特", "犰狳次郎", "魔兽驯养"],
        "content": "鲁迪家在夏利亚庭院开展的魔物驯化实践。证明大森林魔木幼苗（比特）与贝卡利特魔兽（次郎）在自幼利用天敌气息威慑或魔力滋养下能产生对人类的服从依赖，打破世间魔物不可家养的陈规。",
        "timeline": "迷宫与两妻篇",
        "priority": "次要",
        "category": "力量体系",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_04"],
        "note": "格雷拉特家庭特异生态"
    },
    {
        "keywords": ["多妻家庭契约与生活伦理", "多妻相处准则", "格雷拉特家规", "米里斯一夫一妻抵触"],
        "content": "阿斯拉贵族多妻习俗在夏利亚平民家庭的和谐实践。正妻希露菲地位居尊掌握家庭主导，洛琪希互敬互让自重，财务各自独立兼顾共有开销，房事轮流默契，妥善调和了与米里斯教一夫一妻教规的剧烈冲突。",
        "timeline": "迷宫与两妻篇",
        "priority": "次要",
        "category": "社会规则",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["013_07", "013_08"],
        "note": "两妻家庭伦理规范"
    },
    {
        "keywords": ["塞妮丝的神子化微弱共感", "塞妮丝共感", "塞妮丝意念传递", "神子化心智"],
        "content": "塞妮丝在结晶化被吸收魔力后获得的异能表征。虽丧失逻辑语言与现世记忆，但灵魂结构因异质魔力浸润呈现神子倾向，能跨越语言障壁敏锐感应身边人的真实悲喜，并以抚摸微笑给予心灵抚慰。",
        "timeline": "迷宫与两妻篇",
        "priority": "次要",
        "category": "力量体系",
        "reveal_arc": "第13卷后",
        "spoiler": False,
        "source_chapters": ["013_09", "014_02"],
        "note": "塞妮丝失智后的特殊心灵特质"
    }
]

# Stage 5: 空中要塞、转折点四与决战龙神篇 (Vols 14-15, Ages 17-18)
stage5_entries = [
    {
        "keywords": ["鲁迪乌斯", "鲁迪", "泥沼", "龙神部下鲁迪乌斯"],
        "content": "十七至十八岁，家主兼奥尔斯帝德唯一代理人。历经空中要塞晋见、魔大陆采药；转折点四阅读老鲁迪日记彻底识破人神阴谋，为救家眷研制魔导铠决战龙神，战败后臣服奥尔斯帝德，迎娶艾莉丝开启抗神生涯。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_10", "015_08", "015_12", "015_13"],
        "note": "卷14-15状态，彻底决裂人神归顺龙神"
    },
    {
        "keywords": ["龙神奥尔斯帝德", "奥尔斯帝德", "龙神", "七大列强第二位"],
        "content": "七大列强第二位，初代龙神之子。背负百代轮回诛杀人神的宿愿，因诅咒遭全生物憎恶且魔力恢复极其缓慢。击败魔导铠鲁迪与艾莉丝后，认可鲁迪意志与魔力量，收鲁迪为唯一代理人并赐予反人神手环。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["015_08", "015_09", "015_12", "015_13"],
        "note": "奥尔斯帝德与鲁迪正式同盟"
    },
    {
        "keywords": ["艾莉丝", "艾莉丝·格雷拉特", "狂剑王艾莉丝", "第三位妻子"],
        "content": "狂剑王，鲁迪第三位妻子。在剑之圣地苦修五年获赐凤雅龙剑，接获鲁迪绝笔信后孤身狂飙驰援夏利亚，在森林舍身替鲁迪抵挡奥尔斯帝德致命一击；战后与鲁迪解开误会圆房成婚，成为镇守家门的绝对最强武力。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["015_05", "015_09", "015_10", "015_11"],
        "note": "狂剑王归家成为第三任妻子"
    },
    {
        "keywords": ["希露菲叶特", "希露菲", "长妻希露菲", "露西之母"],
        "content": "鲁迪正妻，育有长女露西。在人神危机与鲁迪决战龙神前夕无条件支持鲁迪并誓死相随，做好为鲁迪刺杀人神使徒的觉悟；战后以真挚胸怀接纳艾莉丝作为第三位妻子融入家庭，维系三妻和谐的家庭基石。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_11", "015_07", "015_11"],
        "note": "卷14-15状态"
    },
    {
        "keywords": ["洛琪希", "洛琪希·格雷拉特", "次妻洛琪希", "菈菈之母"],
        "content": "鲁迪第二位妻子，孕育次女菈菈·格雷拉特。在老鲁迪时间线中原注定感染魔石病惨死，现世因老鲁迪日记告警被鲁迪果断扑杀毒鼠而平安避难；战后协助鲁迪分析古代文献与龙神情报，家庭地位不可动摇。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_11", "015_01", "015_07", "015_13"],
        "note": "卷14-15避过死劫"
    },
    {
        "keywords": ["甲龙王佩尔基乌斯", "佩尔基乌斯", "空中要塞之王", "三英雄之一"],
        "content": "四百年前弑杀拉普拉斯的三英雄之一，空中要塞Chaos Breaker之主。麾下统御十二使魔与太古十一精灵，严禁魔族登城。深谋远虑等待拉普拉斯复活，对爱丽儿发起王者品格考验，并在阿托菲决斗中出面镇场。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_01", "014_02", "014_08", "014_09"],
        "note": "空中要塞主人"
    },
    {
        "keywords": ["前川七星", "七星", "现代召唤者", "干涸病幸存者"],
        "content": "现代日本穿越者。在空中要塞突破召唤术第四阶段后突发干涸病（杜莱病）险死，获鲁迪采回索卡司茶救治。在未来日记揭示后，运用现代逻辑提出多重因果律与平行历史分支假说，成为鲁迪最强战略智囊。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_03", "014_04", "015_04"],
        "note": "干涸病治愈与战略分析"
    },
    {
        "keywords": ["人神", "Hitogami", "伪神人神", "幕后黑手人神"],
        "content": "居于无之世界的白色虚无阴谋家。在转折点四撕下伪善假面，企图借由魔石病老鼠扼杀受孕洛琪希以剪除未来龙神死敌；阴谋败露后威逼鲁迪刺杀宿敌奥尔斯帝德，为整部史诗最具欺骗性的核心死敌。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "第14卷第10话",
        "spoiler": True,
        "source_chapters": ["014_10", "014_11", "015_03"],
        "note": "反转：人神彻底转为死敌"
    },
    {
        "keywords": ["老鲁迪", "未来老人", "日记的主人", "时空跳跃者"],
        "content": "来自五十年后崩坏时间线的老年鲁迪乌斯。因盲信人神致使洛琪希、希露菲、艾莉丝相继惨死，在孤独绝望中穷究魔术，不惜耗尽脏器与魔力发动过去转移魔术回到转折点四，交付日记告诫现世鲁迪后力竭含笑离世。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "第14卷第10话",
        "spoiler": True,
        "source_chapters": ["014_10", "014_11", "015_01", "015_02"],
        "note": "拯救现世时间线的关键未来身"
    },
    {
        "keywords": ["不死魔王阿托菲", "阿托菲", "阿托菲拉托菲", "初代北神之妻"],
        "content": "魔大陆加斯罗不死魔王，巴迪冈迪姐姐兼初代北神卡尔曼之妻。肉身拥有近乎无解的超速再生断肢重组能力，性格暴躁好战，逼迫败者服役；在利卡里斯地下决斗中重创鲁迪，后遭佩尔基乌斯前龙门轰击退场。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_06", "014_07", "014_08"],
        "note": "魔大陆不败武斗魔王"
    },
    {
        "keywords": ["奇希莉卡", "奇希莉卡·奇希里斯", "魔界大帝", "识别人眼授予者"],
        "content": "魔界大帝，长年以紫发羊角幼女形象流浪魔大陆。虽赤贫如洗乞讨度日，但拥有全知魔眼洞悉世情；在利卡里斯接受鲁迪丰盛款待后，赐予克里夫「识别眼」，并揭穿第二次人魔大战大陆开裂实为龙神斗神死战之真相。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_06", "014_09"],
        "note": "赋予克里夫识别眼"
    },
    {
        "keywords": ["爱丽儿", "爱丽儿·阿斯拉", "第二公主爱丽儿", "阿斯拉女王候选"],
        "content": "阿斯拉王国第二公主。魔法大学毕业后展开全面归国争储布局，率团造访空中要塞通过佩尔基乌斯王者心量考核，与鲁迪达成生死战略攻守同盟，蓄势待发准备重返阿斯拉争夺王位。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_01", "014_09", "015_05"],
        "note": "卷14-15争储前夜"
    },
    {
        "keywords": ["克里夫", "克里夫·格利摩尔", "识别眼持有者", "解咒学者"],
        "content": "获奇希莉卡赋予「识别眼」后能洞悉全物象魔力流动与疾病机理。结合吸魔石成功研发抑制艾莉娜丽洁诅咒的专用魔道具，彻底解除妻子受孕与失控危机，成为鲁迪阵营不可替代的技术支柱。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "角色",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_09", "015_06", "015_07"],
        "note": "解咒器研发成功"
    },
    {
        "keywords": ["空中要塞 Chaos Breaker", "空中要塞", "混沌破坏者", "佩尔基乌斯城堡"],
        "content": "佩尔基乌斯所有的五十层浮空古代巨城。长年巡航于大陆万米高空，内设太古壁画石室、十二使魔居所与连接全大陆的远古双向转移魔法阵，具隔绝人神侦测的太古结界与强横防御，是抗击拉普拉斯的绝对堡垒。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "地理",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_01", "014_02", "014_09"],
        "note": "卷14空中舞台"
    },
    {
        "keywords": ["转折点四与老鲁迪告诫", "转折点四", "转折点4", "未来日记现世"],
        "content": "甲龙历424年春，人神诱导鲁迪检查地下室图谋释放魔石病老鼠；老鲁迪穿梭时空降临力挽狂澜，彻底撕碎人神假面。现世鲁迪火速扑杀老鼠保全洛琪希与胎儿，彻底逆转全灭命运，开启对抗人神新历史篇章。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "历史",
        "reveal_arc": "第14卷第10话",
        "spoiler": True,
        "source_chapters": ["014_10", "014_11"],
        "note": "全书最大剧情拐点"
    },
    {
        "keywords": ["泥沼与狂剑王决战龙神", "泥沼对龙神", "夏利亚决战", "龙神战役"],
        "content": "甲龙历424年夏利亚森林决战。鲁迪披挂魔导铠一式倾泻饱和核爆与加特林岩炮弹逼龙神拔出神刀；危局下艾莉丝持凤雅龙剑舍命飞扑护卫。战局底定后奥尔斯帝德提出招募，鲁迪归顺龙神结成反神同盟。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "历史",
        "reveal_arc": "第15卷第8-9话",
        "spoiler": True,
        "source_chapters": ["015_08", "015_09"],
        "note": "列强级巅峰决战"
    },
    {
        "keywords": ["鲁迪乌斯归顺龙神麾下", "臣服龙神", "龙神部下", "反人神同盟"],
        "content": "决战后鲁迪乌斯正式向七大列强第二位奥尔斯帝德宣誓效忠。佩戴防人神监控手环，以倾全家之力助爱丽儿争储、阻击人神使徒及为四百年后封印拉普拉斯铺路为己任，成为龙神全权代理人。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "历史",
        "reveal_arc": "第15卷第12-13话",
        "spoiler": True,
        "source_chapters": ["015_12", "015_13"],
        "note": "全书阵营根本转向"
    },
    {
        "keywords": ["未来日记", "老鲁迪日记", "悲惨历史手记", "穿越日记"],
        "content": "老鲁迪耗费数十年血泪写就的残破活页手记。详尽记录洛琪希染魔石病惨死、希露菲惨遭曝尸、艾莉丝替己战死、重力魔术公式及魔导铠图纸，不仅彻底坐实人神死敌面目，更为现世翻盘奠定全套理论技术根基。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "物品",
        "reveal_arc": "第14卷第10话",
        "spoiler": True,
        "source_chapters": ["014_10", "014_11", "015_01", "015_02"],
        "note": "改写命运的因果奇物"
    },
    {
        "keywords": ["魔导铠一式", "魔导铠", "对龙神装甲", "加特林魔导铠"],
        "content": "鲁迪集结札诺巴工坊、克里夫解咒技术与古代自动人偶核心全力打造的三米高重型全覆式战甲。以高密度致密岩石结合合金制成，铭刻全套魔力传导与自愈术式，配十连装岩炮弹加特林，具备列强级攻防机动性。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "物品",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["015_06", "015_07", "015_08"],
        "note": "鲁迪巅峰科技产物"
    },
    {
        "keywords": ["凤雅龙剑", "剑神七剑之一", "破甲水晶剑", "艾莉丝佩剑"],
        "content": "绝世名匠「龙皇」采古代神龙骸骨为初代剑神铸造的剑神七剑之一。剑身透明纯净宛如水晶，具无视斗气防御与穿透高阶护甲的神威，由加尔·法利昂正式赠予晋升剑王的艾莉丝，成为狂剑王专属宝刃。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "物品",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["015_09", "015_11"],
        "note": "狂剑王神兵"
    },
    {
        "keywords": ["初代龙神的神刀", "神刀", "龙神佩刀", "破法神刃"],
        "content": "奥尔斯帝德腰间黑鞘弯刀。乃初代龙神传承之终极神器，非面对列强强敌绝不出鞘。出鞘后斩击无影无形，能轻易斩裂高级复合魔法轰炸与厚重魔导铠甲，蕴含破除世界真理法则的霸绝威能。",
        "timeline": "决战龙神篇",
        "priority": "核心",
        "category": "物品",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["015_08", "015_12"],
        "note": "龙神底牌兵刃"
    },
    {
        "keywords": ["避神干扰手环", "龙神手环", "防人神手环", "遮蔽秘术"],
        "content": "初代龙神以秘术秘制之古老手环。佩戴后能使佩戴者气息与真理共振，彻底从人神的广域未来视与无之世界观测中隐匿隐形，使人神再无法直接窥探或托梦干涉佩戴者，为反抗人神之关键防具。",
        "timeline": "决战龙神篇",
        "priority": "次要",
        "category": "物品",
        "reveal_arc": "第15卷第12话",
        "spoiler": True,
        "source_chapters": ["015_12", "015_15"],
        "note": "龙神赐予鲁迪一家庇护"
    },
    {
        "keywords": ["索卡司茶与干涸病疗法", "索卡司草", "索卡司茶", "杜莱病解药"],
        "content": "魔大陆各大魔王城堡地下培植的珍贵耐阴药草。饮用其煎制之茶汤能迅速疏通人体魔力滞留并促使杂质魔力顺畅排泄，为异世界穿越者罹患杜莱病（干涸病）之唯一特效神药。",
        "timeline": "决战龙神篇",
        "priority": "次要",
        "category": "力量体系",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["014_04", "014_06", "014_09"],
        "note": "挽救七星性命之关键药草"
    },
    {
        "keywords": ["拉普拉斯因子与肉体容器", "拉普拉斯因子", "绿色胎记", "魔力容器"],
        "content": "魔神拉普拉斯战败灵魂粉碎后散落于后世的基因遗传因子。具此因子者往往天生拥有惊人魔力总量与坚韧肉体，但因体质异变天生无法缠绕斗气强化肌肉，鲁迪乌斯天生巨量魔力即源于此因子的极度表达。",
        "timeline": "决战龙神篇",
        "priority": "次要",
        "category": "力量体系",
        "reveal_arc": "第15卷第13话",
        "spoiler": True,
        "source_chapters": ["015_08", "015_13"],
        "note": "龙神揭秘鲁迪庞大魔力根源"
    },
    {
        "keywords": ["三妻家庭同居契约", "三妻家庭", "格雷拉特三妻同盟", "狂犬归宿"],
        "content": "艾莉丝作为第三位妻子加入格雷拉特家后的家族共处体制。希露菲主持大局，洛琪希传道解惑兼谋划，艾莉丝总领武力护卫全宅安全与操练，三女情谊笃厚相互扶持，共创鲁迪最为珍惜的安稳港湾。",
        "timeline": "决战龙神篇",
        "priority": "次要",
        "category": "社会规则",
        "reveal_arc": "",
        "spoiler": False,
        "source_chapters": ["015_11", "015_14"],
        "note": "三妻完整家庭生活成型"
    }
]

# Run validation across all stages
validate_entries(shared_entries, "shared_world")
validate_entries(stage1_entries, "stage1_childhood")
validate_entries(stage2_entries, "stage2_demon_continent")
validate_entries(stage3_entries, "stage3_academy")
validate_entries(stage4_entries, "stage4_labyrinth_family")
validate_entries(stage5_entries, "stage5_dragon_god")

# Write out to world_stages and outputs/world_stages
out_dirs = ["world_stages", "outputs/world_stages"]
for d in out_dirs:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "shared_world.json"), 'w', encoding='utf-8') as f:
        json.dump(shared_entries, f, ensure_ascii=False, indent=2)
    with open(os.path.join(d, "stage1_childhood.json"), 'w', encoding='utf-8') as f:
        json.dump(stage1_entries, f, ensure_ascii=False, indent=2)
    with open(os.path.join(d, "stage2_demon_continent.json"), 'w', encoding='utf-8') as f:
        json.dump(stage2_entries, f, ensure_ascii=False, indent=2)
    with open(os.path.join(d, "stage3_academy.json"), 'w', encoding='utf-8') as f:
        json.dump(stage3_entries, f, ensure_ascii=False, indent=2)
    with open(os.path.join(d, "stage4_labyrinth_family.json"), 'w', encoding='utf-8') as f:
        json.dump(stage4_entries, f, ensure_ascii=False, indent=2)
    with open(os.path.join(d, "stage5_dragon_god.json"), 'w', encoding='utf-8') as f:
        json.dump(stage5_entries, f, ensure_ascii=False, indent=2)

print("All 6 JSON files successfully written!")

# Generate complete world_summary.md
def render_stage_summary(entries, title, desc):
    cores = [e for e in entries if e["priority"] == "核心"]
    secs = [e for e in entries if e["priority"] == "次要"]
    lines = [f"## {title}\n{desc}\n\n**核心条目**：{len(cores)} 条 | **次要条目**：{len(secs)} 条 | **总计**：{len(entries)} 条\n"]
    lines.append("### 核心条目")
    for e in cores:
        kw = ", ".join(e["keywords"][:4])
        lines.append(f"- [{e['category']}] **{e['keywords'][0]}**（关键词：{kw}）")
    lines.append("\n### 次要条目")
    for e in secs:
        kw = ", ".join(e["keywords"][:4])
        lines.append(f"- [{e['category']}] **{e['keywords'][0]}**（关键词：{kw}）")
    lines.append("\n---\n")
    return "\n".join(lines)

summary_md = f"""# 世界书条目总览 (world_summary.md)

基于《无职转生》全 15 卷（201 章节）全量原始设定提取沉淀而成，专为基于时间线的角色扮演（RP）与推演系统设计。包含跨阶段通用底座及五大历史阶段世界书。

---

{render_stage_summary(shared_entries, "一、shared_world.json（跨阶段通用底座 · 始终启用）", "涵盖世界物理、全阶魔术、剑术流派、斗气、七大列强、太古六面世界、吸魔石与神兵名刃法则，始终常驻挂载。")}
{render_stage_summary(stage1_entries, "二、stage1_childhood.json（幼年篇 · 卷1~2 · 3-10岁 · 布耶纳村与罗亚）", "鲁迪幼年启蒙、拜师洛琪希、邂逅希露菲与大小姐艾莉丝，至菲托亚大转移爆发前夕。")}
{render_stage_summary(stage2_entries, "三、stage2_demon_continent.json（魔大陆与归乡长征篇 · 卷3~6 · 10-13岁 · 死胡同流亡长征）", "Dead End三人结成、穿越魔大陆、跨越大森林与米里斯神圣国、初战龙神与艾莉丝离别。")}
{render_stage_summary(stage3_entries, "四、stage3_academy.json（青少年篇 · 泥沼冒险者与魔法大学新婚生活 · 卷7~11 · 13~16岁）", "泥沼独行冒险、入学拉诺亚魔法大学、解开菲兹身世与心魔治愈、结婚购宅与转折点三。")}
{render_stage_summary(stage4_entries, "五、stage4_labyrinth_family.json（转移迷宫救援与两妻家庭篇 · 卷12~13 · 16~17岁）", "贝卡利特转移迷宫死斗、魔石九头龙、保罗阵亡与塞妮丝救出、断臂与迎娶洛琪希、长女露西诞生。")}
{render_stage_summary(stage5_entries, "六、stage5_dragon_god.json（空中要塞、转折点四与决战龙神篇 · 卷14~15 · 17~18岁）", "空中要塞觐见佩尔基乌斯、干涸病救治、转折点四未来老人日记彻底揭穿人神、研制魔导铠死战龙神、狂剑王艾莉丝归位、宣誓臣服龙神为打倒人神展开终身行动。")}

## 七、RP 挂载使用指南与阶段切换标准

1. **常驻挂载（始终启用）**：
   - 必须常驻挂载 `shared_world.json`。
   - 包含世界底层魔术、剑术、斗气、七大列强石碑、神子/咒子、魔眼法则、六面世界构造、吸魔石物理规则、各种族生理及公会铁律等不可动摇之基石。

2. **阶段切换标准（严格单选启用其一，彻底防剧透）**：
   - **幼年探索推演**：加载 `shared_world.json` + `stage1_childhood.json`
   - **魔大陆长征流亡**：加载 `shared_world.json` + `stage2_demon_continent.json`
   - **校园生活与早婚岁月**：加载 `shared_world.json` + `stage3_academy.json`（保罗仍健在，洛琪希仍在贝卡利特，艾莉丝在圣地修行）
   - **迷宫救母与两妻新生活**：加载 `shared_world.json` + `stage4_labyrinth_family.json`（保罗牺牲，鲁迪断臂装义手，洛琪希进门，露西出生，尚未知晓人神阴谋）
   - **决战龙神与抗神霸业**：加载 `shared_world.json` + `stage5_dragon_god.json`（人神死敌面目暴露，魔导铠参战，艾莉丝第三妻归位，鲁迪归顺龙神）
"""

for d in out_dirs:
    with open(os.path.join(d, "world_summary.md"), 'w', encoding='utf-8') as f:
        f.write(summary_md)

print("ALL MERGES COMPLETE! world_summary.md successfully generated!")
