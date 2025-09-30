# main.py (修正版：「空間的シグネチャ」アルゴリズム + エラー修正)

import math
from file_io import parse_uml_file, write_uml_file
from similarity_calculator import SimilarityCalculator
from uml_data import UmlClass, UmlRelation

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

def calculate_centroid(classes):
    if not classes:
        return (0, 0)
    sum_x = sum(cls.x for cls in classes)
    sum_y = sum(cls.y for cls in classes)
    return (sum_x / len(classes), sum_y / len(classes))

def get_spatial_signature(cls, diagram_data):
    signature = []
    class_map = {c.id: c for c in diagram_data["classes"]}
    for rel in diagram_data["relations"]:
        neighbor_cls = None
        if rel.source_id == cls.id and rel.target_id in class_map:
            neighbor_cls = class_map[rel.target_id]
        elif rel.target_id == cls.id and rel.source_id in class_map:
            neighbor_cls = class_map[rel.source_id]
        if neighbor_cls:
            relative_vector = (neighbor_cls.x - cls.x, neighbor_cls.y - cls.y)
            signature.append(relative_vector)
    signature.sort()
    return signature

def compare_signatures(sig_a, sig_b):
    if not sig_a and not sig_b:
        return 1.0
    if not sig_a or not sig_b:
        return 0.0
    def vector_distance(v1, v2):
        return math.sqrt((v1[0] - v2[0])**2 + (v1[1] - v2[1])**2)
    total_distance = 0
    matched_b_indices = set()
    for vec_a in sig_a:
        min_dist = float('inf')
        best_match_idx = -1
        for i, vec_b in enumerate(sig_b):
            if i in matched_b_indices:
                continue
            dist = vector_distance(vec_a, vec_b)
            if dist < min_dist:
                min_dist = dist
                best_match_idx = i
        if best_match_idx != -1:
            total_distance += min_dist
            matched_b_indices.add(best_match_idx)
    avg_distance = total_distance / len(sig_a) if sig_a else 0
    similarity = 1 / (1 + avg_distance / 100)
    len_diff_penalty = 1.0 - (abs(len(sig_a) - len(sig_b)) / max(len(sig_a), len(sig_b)))
    return similarity * len_diff_penalty

def calculate_spatial_similarity_advanced(cls_a, data_a, cls_b, data_b):
    signature_a = get_spatial_signature(cls_a, data_a)
    signature_b = get_spatial_signature(cls_b, data_b)
    return compare_signatures(signature_a, signature_b)

# main.py の find_best_matches 関数のみを修正

def find_best_matches(data_a, data_b, calculator, threshold=0.6, weights=None):
    if weights is None:
        weights = {"semantic": 0.7, "structural": 0.15, "spatial": 0.15}

    classes_a = list(data_a["classes"])
    classes_b = list(data_b["classes"])
    
    # 全てのペアのスコアを事前に計算
    all_scores = []
    for cls_a in classes_a:
        for cls_b in classes_b:
            text_a = cls_a.name + " " + " ".join(cls_a.attributes)
            text_b = cls_b.name + " " + " ".join(cls_b.attributes)
            
            semantic_score = calculator.get_similarity(text_a, text_b)
            structural_score = calculate_structural_similarity(cls_a, cls_b, data_a, data_b)
            spatial_score = calculate_spatial_similarity_advanced(cls_a, data_a, cls_b, data_b)
            
            total_score = (semantic_score * weights["semantic"] +
                           structural_score * weights["structural"] +
                           spatial_score * weights["spatial"])
            
            all_scores.append((total_score, semantic_score, structural_score, spatial_score, cls_a, cls_b))
    
    # 総合スコアで降順にソート
    all_scores.sort(key=lambda x: x[0], reverse=True)
    
    matched_pairs = []
    matched_a_ids = set()
    matched_b_ids = set()
    
    # --- ▼▼▼ 新しい段階的マッチングロジック ▼▼▼ ---
    
    # ステップ1：名前が完全一致するペアを最優先でマッチング
    for score_tuple in list(all_scores):
        cls_a = score_tuple[4]
        cls_b = score_tuple[5]
        if cls_a.name == cls_b.name:
            if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
                matched_pairs.append(score_tuple)
                matched_a_ids.add(cls_a.id)
                matched_b_ids.add(cls_b.id)

    # ステップ2：意味スコアが非常に高いペアを次にマッチング
    high_confidence_threshold = 0.95
    for score_tuple in list(all_scores):
        sem_score = score_tuple[1]
        cls_a = score_tuple[4]
        cls_b = score_tuple[5]
        if sem_score >= high_confidence_threshold:
            if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
                matched_pairs.append(score_tuple)
                matched_a_ids.add(cls_a.id)
                matched_b_ids.add(cls_b.id)

    # ステップ3：残りのクラスで、総合スコアに基づいた通常のマッチングを行う
    for score_tuple in list(all_scores):
        total_score = score_tuple[0]
        cls_a = score_tuple[4]
        cls_b = score_tuple[5]
        if total_score >= threshold:
            if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
                matched_pairs.append(score_tuple)
                matched_a_ids.add(cls_a.id)
                matched_b_ids.add(cls_b.id)
            
    # --- ▲▲▲ 新ロジックここまで ▲▲▲ ---

    unmatched_a = [cls for cls in classes_a if cls.id not in matched_a_ids]
    unmatched_b = [cls for cls in classes_b if cls.id not in matched_b_ids]
    
    # 表示のために、最終的なマッチング結果をスコアでソート
    matched_pairs.sort(key=lambda x: x[0], reverse=True)
    
    return matched_pairs, unmatched_a, unmatched_b, all_scores
def merge_uml_data(matches, unmatched_a, unmatched_b, relations_a, relations_b):
    merged_classes = []
    merged_relations = []
    id_map_a = {}
    id_map_b = {}
    new_id_counter = 1
    for _, _, _, _, cls_a, cls_b in matches:
        merged_attrs = sorted(list(set(cls_a.attributes + cls_b.attributes)))
        merged_x = (cls_a.x + cls_b.x) // 2
        merged_y = (cls_a.y + cls_b.y) // 2
        new_class = UmlClass(str(new_id_counter), cls_a.name, merged_attrs, merged_x, merged_y)
        merged_classes.append(new_class)
        id_map_a[cls_a.id] = new_class.id
        id_map_b[cls_b.id] = new_class.id
        new_id_counter += 1
    for cls in unmatched_a:
        new_class = UmlClass(str(new_id_counter), cls.name, cls.attributes, cls.x, cls.y)
        merged_classes.append(new_class)
        id_map_a[cls.id] = new_class.id
        new_id_counter += 1
    for cls in unmatched_b:
        new_class = UmlClass(str(new_id_counter), cls.name, cls.attributes, cls.x, cls.y)
        merged_classes.append(new_class)
        id_map_b[cls.id] = new_class.id
        new_id_counter += 1
    all_relations = relations_a + relations_b
    for rel in all_relations:
        id_map = id_map_a if rel in relations_a else id_map_b
        new_source_id = id_map.get(rel.source_id)
        new_target_id = id_map.get(rel.target_id)
        if new_source_id and new_target_id:
            new_relation = UmlRelation(str(len(merged_relations) + 1), new_source_id, new_target_id)
            merged_relations.append(new_relation)
    return {"classes": merged_classes, "relations": merged_relations}


# --- 実行部分 ---
data_a = parse_uml_file("dataA.txt")
data_b = parse_uml_file("dataB.txt")
if data_a and data_b:
    calculator = SimilarityCalculator()
    if calculator.model:
        matches, unmatched_a, unmatched_b, all_class_scores = find_best_matches(
            data_a, data_b, calculator, threshold=0.6
        )
        print("\n--- 全てのクラスペアの類似度スコア一覧 ---")
        print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<20}{'Class B':<20}")
        print("-" * 80)
        for score, sem, stru, spa, cls_a, cls_b in all_class_scores:
            print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<20}{cls_b.name:<20}")
        print("\n--- 統合スコアに基づくマッチング候補 ---")
        if matches:
            print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<20}{'Class B':<20}")
            print("-" * 80)
            for score, sem, stru, spa, cls_a, cls_b in matches:
                print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<20}{cls_b.name:<20}")
        else:
            print("基準を超えるマッチング候補は見つかりませんでした。")
        print("\n--- マッチングされなかったクラス ---")
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
        print("\n--- マージ処理を実行中... ---")
        merged_data = merge_uml_data(matches, unmatched_a, unmatched_b, data_a["relations"], data_b["relations"])
        output_filename = "data_merged.txt"
        write_uml_file(output_filename, merged_data)
        print(f"マージが完了し、'{output_filename}' に結果を保存しました。")