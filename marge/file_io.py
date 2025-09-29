# file_io.py (修正版)

import re
from uml_data import UmlClass, UmlRelation

def parse_uml_file(file_path):
    """クラス図ファイルを解析して、オブジェクトのリストに変換する"""
    classes = []
    relations = []
    
    # 【修正点】属性部分(.*)をより柔軟に受け取り、属性がないクラスにも対応
    class_pattern = re.compile(r"<(\d+)>]Class\$\((\d+),(\d+)\)!(.*)!!(.*);")
    relation_pattern = re.compile(r"<(\d+)>]ClassRelationLink\$<(\d+)>!<(\d+)>!.*")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                class_match = class_pattern.match(line)
                if class_match:
                    id, x, y, name, attrs_part = class_match.groups()
                    
                    attributes = []
                    # 属性パートが存在するかチェック
                    if attrs_part.startswith('-'):
                        # 先頭の'-'と末尾の'%;'を取り除く
                        clean_attrs = attrs_part.strip('-%!;')
                        if clean_attrs:
                            attributes = clean_attrs.split('%-')
                            
                    classes.append(UmlClass(id, name, attributes, int(x), int(y)))
                    continue

                relation_match = relation_pattern.match(line)
                if relation_match:
                    id, source_id, target_id = relation_match.groups()
                    relations.append(UmlRelation(id, source_id, target_id))

    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
        return None

    return {"classes": classes, "relations": relations}
# file_io.py に追記

def write_uml_file(file_path, uml_data):
    """プログラム上のデータをクラス図ファイル形式で書き出す"""
    lines = []
    
    # クラス情報を文字列に変換
    for uml_class in uml_data["classes"]:
        # 属性リストを '%-' で連結して文字列に戻す
        attrs_str = "%-".join(uml_class.attributes)
        if attrs_str:
            attrs_str += "%" # 末尾に % を付ける
        
        # 元のフォーマットに従って文字列を組み立てる
        line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!-{attrs_str};"
        lines.append(line)

    # 関連情報を文字列に変換 (今回は主要部分のみを再現)
    for uml_relation in uml_data["relations"]:
        line = f"<{uml_relation.id}>]ClassRelationLink$<{uml_relation.source_id}>!<" \
               f"{uml_relation.target_id}>!SimpleRelation!!Solid!None!0..*!!!None!1!!;"
        lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))