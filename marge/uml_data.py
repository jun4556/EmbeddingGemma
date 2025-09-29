# uml_data.py という名前で保存すると良いでしょう

class UmlClass:
    """クラスの情報を保持するクラス"""
    def __init__(self, id, name, attributes, x=0, y=0):
        self.id = id
        self.name = name
        self.attributes = attributes
        self.x = x  # 座標X
        self.y = y  # 座標Y

    def __repr__(self):
        # print()で中身を確認しやすくするための記述
        return f"Class(id={self.id}, name='{self.name}', attributes={self.attributes})"

class UmlRelation:
    """関連の情報を保持するクラス"""
    def __init__(self, id, source_id, target_id):
        self.id = id
        self.source_id = source_id  # 関連の開始元クラスID
        self.target_id = target_id  # 関連の終着点クラスID

    def __repr__(self):
        return f"Relation(id={self.id}, source={self.source_id}, target={self.target_id})"