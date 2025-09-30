# file_io.py (修正版)

import re
from uml_data import UmlClass, UmlRelation

def parse_uml_file(file_path):
    """クラス図ファイルを解析して、オブジェクトのリストに変換する"""
    classes = []
    relations = []
    
    # 【修正点】正規表現を修正し、属性がない'!!!'の形式にも対応
    # クラス名(非貪欲マッチ)と、その後のセパレータ以降の文字列をキャプチャする
    class_pattern = re.compile(r"<(\d+)>]Class\$\((\d+),(\d+)\)!(.*?)!(.*);")
    relation_pattern = re.compile(r"<(\d+)>]ClassRelationLink\$<(\d+)>!<(\d+)>!.*")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                class_match = class_pattern.match(line)
                if class_match:
                    id, x, y, name, rest = class_match.groups()
                    # restには '!!-属性1%-属性2%' または '!!' が入る
                    
                    attributes = []
                    # 【修正点】属性部分の判定をより厳密に
                    # 属性がある場合、restは'!-...'で始まる
                    if rest.startswith('!-'):
                        # 先頭の'!-'と、もしあれば末尾の'%'を取り除く
                        attrs_str = rest[2:]
                        if attrs_str.endswith('%'):
                            attrs_str = attrs_str[:-1]
                        
                        if attrs_str:
                            attributes = attrs_str.split('%-')
                            
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

def write_uml_file(file_path, uml_data):
    """プログラム上のデータをクラス図ファイル形式で書き出す"""
    lines = []
    
    # クラス情報を文字列に変換
    for uml_class in uml_data["classes"]:
        # 【修正点】属性の有無でフォーマットを分岐
        if uml_class.attributes:
            # 属性がある場合: !!-属性1%-属性2%;
            attrs_str = "%-".join(uml_class.attributes)
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!-{attrs_str}%;"
        else:
            # 属性がない場合: !!!;
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!!;"
        lines.append(line)

    # 関連情報を文字列に変換 (今回は主要部分のみを再現)
    for uml_relation in uml_data["relations"]:
        line = f"<{uml_relation.id}>]ClassRelationLink$<{uml_relation.source_id}>!<" \
               f"{uml_relation.target_id}>!SimpleRelation!!Solid!None!0..*!!!None!1!!;"
        lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))