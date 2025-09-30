# uml_data.py (修正版)

class UmlClass:
    """クラスの情報を保持するクラス"""
    def __init__(self, id, name, attributes, x=0, y=0):
        self.id = id
        self.name = name
        self.attributes = attributes
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Class(id={self.id}, name='{self.name}', attributes={self.attributes})"

# ▼▼▼ 変更点 ▼▼▼
class UmlRelation:
    """関連の情報を保持するクラス"""
    def __init__(self, id, source_id, target_id, rel_type='SimpleRelation',
                 source_multi='None', target_multi='None'):
        self.id = id
        self.source_id = source_id
        self.target_id = target_id
        self.type = rel_type
        self.source_multiplicity = source_multi
        self.target_multiplicity = target_multi

    def __repr__(self):
        return (f"Relation(id={self.id}, type='{self.type}', "
                f"source={self.source_id}[{self.source_multiplicity}], "
                f"target={self.target_id}[{self.target_multiplicity}])")
# ▲▲▲ 変更点 ▲▲▲