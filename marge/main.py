# main.py (Relationalスコアを非表示にする修正版)

import math
from file_io import parse_uml_file, write_uml_file
from similarity_calculator import SimilarityCalculator
from uml_data import UmlClass, UmlRelation

# --- 省略 (get_relations_for_class, calculate_structural_similarity, calculate_centroid, 
#            get_spatial_signature, compare_signatures, calculate_spatial_similarity_advanced は変更なし) ---
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


# 関連類似度計算の関数群 (変更なし)
RELATION_TYPE_SIMILARITY = {
    "Composition": {"Aggregation": 0.8, "Association": 0.5},
    "Aggregation": {"Composition": 0.8, "Association": 0.6},
    "Association": {"Composition": 0.5, "Aggregation": 0.6, "SimpleRelation": 0.4},
    "Generalization": {"Realization": 0.7},
    "Realization": {"Generalization": 0.7},
}

def get_relation_type_similarity(type1, type2):
    if type1 == type2:
        return 1.0
    if type1 in RELATION_TYPE_SIMILARITY and type2 in RELATION_TYPE_SIMILARITY[type1]:
        return RELATION_TYPE_SIMILARITY[type1][type2]
    if type2 in RELATION_TYPE_SIMILARITY and type1 in RELATION_TYPE_SIMILARITY[type2]:
        return RELATION_TYPE_SIMILARITY[type2][type1]
    return 0.0

def get_multiplicity_similarity(multi1, multi2):
    return 1.0 if multi1 == multi2 else 0.0

def get_all_relations_for_class(class_id, relations):
    return [rel for rel in relations if rel.source_id == class_id or rel.target_id == class_id]

def calculate_relational_similarity(cls_a, data_a, cls_b, data_b):
    relations_a = get_all_relations_for_class(cls_a.id, data_a["relations"])
    relations_b = get_all_relations_for_class(cls_b.id, data_b["relations"])

    if not relations_a and not relations_b:
        return 1.0
    if not relations_a or not relations_b:
        return 0.0

    total_max_score = 0
    matched_b_indices = set()

    for rel_a in relations_a:
        max_score = -1.0
        best_match_idx = -1
        for i, rel_b in enumerate(relations_b):
            if i in matched_b_indices:
                continue
            
            type_sim = get_relation_type_similarity(rel_a.type, rel_b.type)
            source_multi_sim = get_multiplicity_similarity(rel_a.source_multiplicity, rel_b.source_multiplicity)
            target_multi_sim = get_multiplicity_similarity(rel_a.target_multiplicity, rel_b.target_multiplicity)
            
            current_score = 0.6 * type_sim + 0.4 * ((source_multi_sim + target_multi_sim) / 2)
            
            if current_score > max_score:
                max_score = current_score
                best_match_idx = i
        
        if best_match_idx != -1:
            total_max_score += max_score
            matched_b_indices.add(best_match_idx)

    avg_score = total_max_score / len(relations_a) if relations_a else 0
    len_diff_penalty = 1.0 - (abs(len(relations_a) - len(relations_b)) / max(len(relations_a), len(relations_b)))
    
    return avg_score * len_diff_penalty


def find_best_matches(data_a, data_b, calculator, threshold=0.6, weights=None):
    if weights is None:
        weights = {"semantic": 0.7, "relational": 0.0, "structural": 0.15, "spatial": 0.15} 

    classes_a = list(data_a["classes"])
    classes_b = list(data_b["classes"])
    
    all_scores = []
    for cls_a in classes_a:
        for cls_b in classes_b:
            text_a = cls_a.name + " " + " ".join(cls_a.attributes)
            text_b = cls_b.name + " " + " ".join(cls_b.attributes)
            
            semantic_score = calculator.get_similarity(text_a, text_b)
            structural_score = calculate_structural_similarity(cls_a, cls_b, data_a, data_b)
            spatial_score = calculate_spatial_similarity_advanced(cls_a, data_a, cls_b, data_b)
            relational_score = calculate_relational_similarity(cls_a, data_a, cls_b, data_b)
            
            total_score = (semantic_score * weights["semantic"] +
                           relational_score * weights["relational"] +
                           structural_score * weights["structural"] +
                           spatial_score * weights["spatial"])
            
            # Relationalスコアも内部的には保持するが、表示はしない
            all_scores.append((total_score, semantic_score, relational_score, structural_score, spatial_score, cls_a, cls_b))
    
    all_scores.sort(key=lambda x: x[0], reverse=True)
    
    matched_pairs = []
    matched_a_ids = set()
    matched_b_ids = set()
    
    # 段階的マッチングロジック (省略)
    for score_tuple in list(all_scores):
        cls_a = score_tuple[5]
        cls_b = score_tuple[6]
        if cls_a.name == cls_b.name:
            if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
                matched_pairs.append(score_tuple)
                matched_a_ids.add(cls_a.id)
                matched_b_ids.add(cls_b.id)

    high_confidence_threshold = 0.95
    for score_tuple in list(all_scores):
        sem_score = score_tuple[1]
        cls_a = score_tuple[5]
        cls_b = score_tuple[6]
        if sem_score >= high_confidence_threshold:
            if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
                matched_pairs.append(score_tuple)
                matched_a_ids.add(cls_a.id)
                matched_b_ids.add(cls_b.id)

    for score_tuple in list(all_scores):
        total_score = score_tuple[0]
        cls_a = score_tuple[5]
        cls_b = score_tuple[6]
        if total_score >= threshold:
            if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
                matched_pairs.append(score_tuple)
                matched_a_ids.add(cls_a.id)
                matched_b_ids.add(cls_b.id)
            
    unmatched_a = [cls for cls in classes_a if cls.id not in matched_a_ids]
    unmatched_b = [cls for cls in classes_b if cls.id not in matched_b_ids]
    
    matched_pairs.sort(key=lambda x: x[0], reverse=True)
    
    return matched_pairs, unmatched_a, unmatched_b, all_scores

# merge_uml_data は変更なし
def merge_uml_data(matches, unmatched_a, unmatched_b, relations_a, relations_b):
    merged_classes = []
    merged_relations = []
    id_map_a = {}
    id_map_b = {}
    new_id_counter = 1
    for _, _, _, _, _, cls_a, cls_b in matches:
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
        
    processed_relations = set()
    
    def add_relation_if_new(rel, id_map):
        new_source_id = id_map.get(rel.source_id)
        new_target_id = id_map.get(rel.target_id)
        
        rel_key = tuple(sorted((new_source_id, new_target_id)))
        
        if new_source_id and new_target_id and rel_key not in processed_relations:
            new_relation = UmlRelation(str(len(merged_relations) + 1),
                                       new_source_id, new_target_id,
                                       rel.type, rel.source_multiplicity,
                                       rel.target_multiplicity)
            merged_relations.append(new_relation)
            processed_relations.add(rel_key)

    all_original_relations = relations_a + relations_b
    for rel in all_original_relations:
        id_map = id_map_a if rel in relations_a else id_map_b
        add_relation_if_new(rel, id_map)
        
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
        # ▼▼▼ 変更点：Relationalをヘッダと表示から削除 ▼▼▼
        print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<20}{'Class B':<20}")
        print("-" * 78)
        # score_tupleの3番目(relational_score)をアンダースコア(_)で無視する
        for score, sem, _, stru, spa, cls_a, cls_b in all_class_scores:
            print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<20}{cls_b.name:<20}")
        # ▲▲▲ 変更点 ▲▲▲

        print("\n--- 統合スコアに基づくマッチング候補 ---")
        if matches:
            # ▼▼▼ 変更点：Relationalをヘッダと表示から削除 ▼▼▼
            print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<20}{'Class B':<20}")
            print("-" * 78)
            # score_tupleの3番目(relational_score)をアンダースコア(_)で無視する
            for score, sem, _, stru, spa, cls_a, cls_b in matches:
                print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<20}{cls_b.name:<20}")
            # ▲▲▲ 変更点 ▲▲▲
        else:
            print("基準を超えるマッチング候補は見つかりませんでした。")

        # 未マッチクラスの表示 (変更なし)
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