# main.py (最終版：マージ機能を追加)

import math
# write_uml_file をインポートする
from file_io import parse_uml_file, write_uml_file
from similarity_calculator import SimilarityCalculator
from uml_data import UmlClass, UmlRelation # UmlClassとUmlRelationを直接使うためインポート

# --- 既存の類似度計算関数（変更なし）---

def get_relations_for_class(class_id, relations):
    related = {"source": [], "target": []}
    for rel in relations:
        if rel.source_id == class_id:
            related["source"].append(rel)
        if rel.target_id == class_id:
            related["target"].append(rel)
    return related

def calculate_structural_similarity(cls_a, cls_b, data_a, data_b):
    relations_a = get_relations_for_class(cls_a.id, data_a["relations"])
    relations_b = get_relations_for_class(cls_b.id, data_b["relations"])
    source_count_a = len(relations_a["source"])
    source_count_b = len(relations_b["source"])
    target_count_a = len(relations_a["target"])
    target_count_b = len(relations_b["target"])
    source_diff = abs(source_count_a - source_count_b) / max(1, source_count_a + source_count_b)
    target_diff = abs(target_count_a - target_count_b) / max(1, target_count_a + target_count_b)
    similarity = 1.0 - (source_diff + target_diff) / 2
    return similarity

def calculate_spatial_signature(cls, all_classes):
    min_dist = float('inf')
    nearest_vector = (0, 0)
    if len(all_classes) <= 1:
        return nearest_vector
    for other_cls in all_classes:
        if cls.id == other_cls.id:
            continue
        dist = math.sqrt((cls.x - other_cls.x)**2 + (cls.y - other_cls.y)**2)
        if dist < min_dist:
            min_dist = dist
            norm = math.sqrt((other_cls.x - cls.x)**2 + (other_cls.y - cls.y)**2)
            if norm > 0:
                nearest_vector = ((other_cls.x - cls.x) / norm, (other_cls.y - cls.y) / norm)
            else:
                nearest_vector = (0,0)
    return nearest_vector

def calculate_spatial_similarity(cls_a, cls_b, data_a, data_b):
    vector_a = calculate_spatial_signature(cls_a, data_a["classes"])
    vector_b = calculate_spatial_signature(cls_b, data_b["classes"])
    dot_product = vector_a[0] * vector_b[0] + vector_a[1] * vector_b[1]
    return (dot_product + 1) / 2

def find_best_matches(data_a, data_b, calculator, threshold=0.7, weights=None):
    if weights is None:
        weights = {"semantic": 0.6, "structural": 0.2, "spatial": 0.2}
    classes_a = list(data_a["classes"])
    classes_b = list(data_b["classes"])
    all_scores = []
    for cls_a in classes_a:
        for cls_b in classes_b:
            text_a = cls_a.name + " " + " ".join(cls_a.attributes)
            text_b = cls_b.name + " " + " ".join(cls_b.attributes)
            semantic_score = calculator.get_similarity(text_a, text_b)
            structural_score = calculate_structural_similarity(cls_a, cls_b, data_a, data_b)
            spatial_score = calculate_spatial_similarity(cls_a, cls_b, data_a, data_b)
            total_score = (semantic_score * weights["semantic"] +
                           structural_score * weights["structural"] +
                           spatial_score * weights["spatial"])
            all_scores.append((total_score, semantic_score, structural_score, spatial_score, cls_a, cls_b))
    all_scores.sort(key=lambda x: x[0], reverse=True)
    matched_pairs = []
    matched_a_ids = set()
    matched_b_ids = set()
    for score, sem, stru, spa, cls_a, cls_b in all_scores:
        if score >= threshold and cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
            matched_pairs.append((score, sem, stru, spa, cls_a, cls_b))
            matched_a_ids.add(cls_a.id)
            matched_b_ids.add(cls_b.id)
    unmatched_a = [cls for cls in classes_a if cls.id not in matched_a_ids]
    unmatched_b = [cls for cls in classes_b if cls.id not in matched_b_ids]
    return matched_pairs, unmatched_a, unmatched_b, all_scores

# --- ▼ここからが追加部分▼ ---

def merge_uml_data(matches, unmatched_a, unmatched_b, relations_a, relations_b):
    """マッチング結果を基にUMLデータをマージする"""
    merged_classes = []
    merged_relations = []
    id_map_a = {}  # Aの旧ID -> 新ID
    id_map_b = {}  # Bの旧ID -> 新ID
    new_id_counter = 1

    # 1. マッチしたクラスをマージ
    for _, _, _, _, cls_a, cls_b in matches:
        # 属性を統合（重複なし）
        merged_attrs = sorted(list(set(cls_a.attributes + cls_b.attributes)))
        # 座標を平均化
        merged_x = (cls_a.x + cls_b.x) // 2
        merged_y = (cls_a.y + cls_b.y) // 2
        
        new_class = UmlClass(str(new_id_counter), cls_a.name, merged_attrs, merged_x, merged_y)
        merged_classes.append(new_class)
        
        # IDの対応関係を記録
        id_map_a[cls_a.id] = new_class.id
        id_map_b[cls_b.id] = new_class.id
        new_id_counter += 1

    # 2. マッチしなかったクラス(A)を追加
    for cls in unmatched_a:
        new_class = UmlClass(str(new_id_counter), cls.name, cls.attributes, cls.x, cls.y)
        merged_classes.append(new_class)
        id_map_a[cls.id] = new_class.id
        new_id_counter += 1
        
    # 3. マッチしなかったクラス(B)を追加
    for cls in unmatched_b:
        new_class = UmlClass(str(new_id_counter), cls.name, cls.attributes, cls.x, cls.y)
        merged_classes.append(new_class)
        id_map_b[cls.id] = new_class.id
        new_id_counter += 1
        
    # 4. 関連を新しいIDで再構築
    all_relations = relations_a + relations_b
    for rel in all_relations:
        # 元の関連がどちらの図に属していたかで、使うIDマップを切り替える
        id_map = id_map_a if rel in relations_a else id_map_b
        
        new_source_id = id_map.get(rel.source_id)
        new_target_id = id_map.get(rel.target_id)
        
        if new_source_id and new_target_id:
            # 新しいIDが見つかった場合のみ関連を追加
            new_relation = UmlRelation(str(len(merged_relations) + 1), new_source_id, new_target_id)
            merged_relations.append(new_relation)
            
    return {"classes": merged_classes, "relations": merged_relations}

# --- ▲ここまでが追加部分▲ ---


# --- 実行部分 ---

# 1. 2つのファイルを読み込む
data_a = parse_uml_file("dataA.txt")
data_b = parse_uml_file("dataB.txt")

if data_a and data_b:
    # 2. 類似度計算機を準備
    calculator = SimilarityCalculator()

    if calculator.model:
        # 3. マッチング処理
        matches, unmatched_a, unmatched_b, all_class_scores = find_best_matches(
            data_a, data_b, calculator, threshold=0.6
        )

        # 4. 全ての組み合わせの類似度を計算し、一覧表示する
        print("\n--- 全てのクラスペアの類似度スコア一覧 ---")
        print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<20}{'Class B':<20}")
        print("-" * 80)
        for score, sem, stru, spa, cls_a, cls_b in all_class_scores:
            print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<20}{cls_b.name:<20}")

        # 5. 閾値に基づいたマッチング候補と、されなかったものを表示する
        print("\n--- 統合スコアに基づくマッチング候補 ---")
        if matches:
            # (表示部分は省略しません)
            print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<20}{'Class B':<20}")
            print("-" * 80)
            for score, sem, stru, spa, cls_a, cls_b in matches:
                print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<20}{cls_b.name:<20}")
        else:
            print("基準を超えるマッチング候補は見つかりませんでした。")
        
        # (表示部分は省略しません)
        print("\n--- マッチングされなかったクラス ---")
        # ... (既存の表示コード)
        if not unmatched_a and not unmatched_b:
            print("全てのクラスがマッチングされました。")
        else:
            if unmatched_a:
                print("図Aの未マッチクラス:")
                for cls in unmatched_a:
                    print(f"  - {cls.name}")
            if unmatched_b:
                print("図Bの未マッチクラス:")
                for cls in unmatched_b:
                    print(f"  - {cls.name}")

        # --- ▼ここからが追加部分▼ ---
        # 6. マージ処理の実行とファイルへの書き出し
        print("\n--- マージ処理を実行中... ---")
        merged_data = merge_uml_data(matches, unmatched_a, unmatched_b, data_a["relations"], data_b["relations"])
        
        output_filename = "data_merged.txt"
        write_uml_file(output_filename, merged_data)
        
        print(f"マージが完了し、'{output_filename}' に結果を保存しました。")
        # --- ▲ここまでが追加部分▲ ---