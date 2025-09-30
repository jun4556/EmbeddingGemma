# file_io.py (修正版)

import re
from uml_data import UmlClass, UmlRelation

def parse_uml_file(file_path):
    """クラス図ファイルを解析して、オブジェクトのリストに変換する"""
    classes = []
    relations = []
    
    class_pattern = re.compile(r"<(\d+)>]Class\$\((\d+),(\d+)\)!(.*?)!(.*);")
    
    # ▼▼▼ 変更点 ▼▼▼
    # 関連の種類、多重度をキャプチャするよう正規表現を強化
    relation_pattern = re.compile(
        r"<(\d+)>]ClassRelationLink\$<(\d+)>!<(\d+)>!"  # IDs
        r"([^!]*)!!"  # Relation Type
        r"[^!]*![^!]*!"  # Styles (skip)
        r"([^!]*)!!!"  # Source Multiplicity
        r"[^!]*!"  # Role (skip)
        r"([^!]*)!!;"  # Target Multiplicity
    )
    # ▲▲▲ 変更点 ▲▲▲

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
                        if attrs_str.endswith('%'):
                            attrs_str = attrs_str[:-1]
                        if attrs_str:
                            attributes = attrs_str.split('%-')
                    classes.append(UmlClass(id, name, attributes, int(x), int(y)))
                    continue

                relation_match = relation_pattern.match(line)
                if relation_match:
                    # ▼▼▼ 変更点 ▼▼▼
                    id, source_id, target_id, rel_type, source_multi, target_multi = relation_match.groups()
                    # 'None'という文字列はNoneに変換せず、そのまま扱う
                    relations.append(UmlRelation(id, source_id, target_id, rel_type, source_multi, target_multi))
                    # ▲▲▲ 変更点 ▲▲▲

    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
        return None

    return {"classes": classes, "relations": relations}


def write_uml_file(file_path, uml_data):
    """プログラム上のデータをクラス図ファイル形式で書き出す"""
    lines = []
    
    for uml_class in uml_data["classes"]:
        if uml_class.attributes:
            attrs_str = "%-".join(uml_class.attributes)
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!-{attrs_str}%;"
        else:
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!!;"
        lines.append(line)

    # ▼▼▼ 変更点 ▼▼▼
    # 保存された関連情報を使って行を再構築（一部固定値で簡略化）
    for rel in uml_data["relations"]:
        rel_type = rel.type if rel.type else 'SimpleRelation'
        source_multi = rel.source_multiplicity if rel.source_multiplicity else 'None'
        target_multi = rel.target_multiplicity if rel.target_multiplicity else 'None'

        # 関連の種類に応じてスタイルを簡易的に設定
        style = "Solid!SolidArrow" # Default: Generalization
        if rel_type == "Realization":
            style = "LongDashed!SolidArrow"
        elif rel_type == "Dependency":
            style = "Dashed!WireArrow"
        elif rel_type == "Aggregation":
            style = "Solid!SolidDiamond"
        elif rel_type == "Composition":
            style = "Solid!InvertedSolidDiamond"
        elif "Association" in rel_type:
            style = "Solid!WireArrow"
        elif rel_type == "SimpleRelation":
             style = "Solid!None"

        line = (f"<{rel.id}>]ClassRelationLink\$<{rel.source_id}>!<"
                f"{rel.target_id}>!{rel_type}!!{style}!{source_multi}!!!"
                f"None!{target_multi}!!;")
        lines.append(line)
    # ▲▲▲ 変更点 ▲▲▲

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))