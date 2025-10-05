# file_io.py (関連の書き出し処理を完全に修正)

import re
from uml_data import UmlClass, UmlRelation

def parse_uml_file(file_path):
    # ... (この関数は変更ありません)
    classes = []
    relations = []
    
    class_pattern = re.compile(r"<(\d+)>]Class\$\((\d+),(\d+)\)!(.*?)!(.*);")
    relation_pattern = re.compile(
        r"<(\d+)>]ClassRelationLink\$<(\d+)>!<(\d+)>!"
        r"([^!]*)!!"
        r"[^!]*![^!]*!"
        r"([^!]*)!!!"
        r"[^!]*!"
        r"([^!]*)!!;"
    )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                class_match = class_pattern.match(line)
                if class_match:
                    id, x, y, name, rest = class_match.groups()
                    attributes = []
                    if rest.startswith('!-'):
                        attrs_str = rest[2:]
                        raw_attributes = attrs_str.split('%-')
                        attributes = [re.sub(r'[%!]+$', '', attr).strip() for attr in raw_attributes if attr.strip()]

                    classes.append(UmlClass(id, name, attributes, int(x), int(y)))
                    continue

                relation_match = relation_pattern.match(line)
                if relation_match:
                    id, source_id, target_id, rel_type, source_multi, target_multi = relation_match.groups()
                    relations.append(UmlRelation(id, source_id, target_id, rel_type, source_multi, target_multi))

    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
        return None

    return {"classes": classes, "relations": relations}


def write_uml_file(file_path, uml_data):
    """プログラム上のデータをクラス図ファイル形式で書き出す（描画可能な形式に修正）"""
    lines = []
    
    for uml_class in uml_data["classes"]:
        if uml_class.attributes:
            attrs_str = "%-".join(uml_class.attributes)
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!-{attrs_str}%;"
        else:
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!!;"
        lines.append(line)

    # ▼▼▼ 修正箇所: 関連の書き出しロジックを全面的に刷新 ▼▼▼
    for rel in uml_data["relations"]:
        rel_type = rel.type if rel.type else 'SimpleRelation'
        source_multi = rel.source_multiplicity if rel.source_multiplicity else 'None'
        target_multi = rel.target_multiplicity if rel.target_multiplicity else 'None'

        # スタイルと矢印の形状を分離して定義
        line_style = "Solid"
        source_arrow = "None"
        target_arrow = "None" # デフォルト

        if rel_type == "Generalization":
            target_arrow = "SolidArrow"
        elif rel_type == "Realization":
            line_style = "LongDashed"
            target_arrow = "SolidArrow"
        elif rel_type == "Dependency":
            line_style = "Dashed"
            target_arrow = "WireArrow"
        elif rel_type == "Aggregation":
            target_arrow = "SolidDiamond"
        elif rel_type == "Composition":
            target_arrow = "InvertedSolidDiamond"
        elif "Association" in rel_type:
            target_arrow = "WireArrow"
        
        # 描画可能なデータの正しい構文に合わせる
        style_part = f"{line_style}!{source_arrow}"
        
        line = (f"<{rel.id}>]ClassRelationLink$<{rel.source_id}>!<"
                f"{rel.target_id}>!{rel_type}!!{style_part}!{source_multi}!!!"
                f"{target_arrow}!{target_multi}!!;")
        lines.append(line)
    # ▲▲▲ 修正箇所 ▲▲▲

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("".join(lines))