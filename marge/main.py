# main.py (IDの再割り当てロジックを修正した最終版)

import math
import re
from file_io import parse_uml_file, write_uml_file
from similarity_calculator import SimilarityCalculator
from uml_data import UmlClass, UmlRelation

# --- 類似度計算関数群 (変更なし) ---
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
    if not sig_a and not sig_b: return 1.0
    if not sig_a or not sig_b: return 0.0
    def vector_distance(v1, v2):
        return math.sqrt((v1[0] - v2[0])**2 + (v1[1] - v2[1])**2)
    total_distance = 0
    matched_b_indices = set()
    for vec_a in sig_a:
        min_dist = float('inf')
        best_match_idx = -1
        for i, vec_b in enumerate(sig_b):
            if i in matched_b_indices: continue
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

# --- find_best_matches (変更なし) ---
def find_best_matches(data_a, data_b, calculator, threshold=0.6, weights=None):
    if weights is None:
        weights = {"semantic": 0.7, "relational": 0.0, "structural": 0.15, "spatial": 0.15}
    classes_a, classes_b = list(data_a["classes"]), list(data_b["classes"])
    all_scores = []
    for cls_a in classes_a:
        for cls_b in classes_b:
            text_a = f"{cls_a.name} {' '.join(cls_a.attributes)}"
            text_b = f"{cls_b.name} {' '.join(cls_b.attributes)}"
            semantic_score = calculator.get_similarity(text_a, text_b)
            structural_score = calculate_structural_similarity(cls_a, cls_b, data_a, data_b)
            spatial_score = calculate_spatial_similarity_advanced(cls_a, data_a, cls_b, data_b)
            total_score = (semantic_score * weights["semantic"] +
                           structural_score * weights["structural"] +
                           spatial_score * weights["spatial"])
            all_scores.append((total_score, semantic_score, 0.0, structural_score, spatial_score, cls_a, cls_b))
    all_scores.sort(key=lambda x: x[0], reverse=True)
    matched_pairs, matched_a_ids, matched_b_ids = [], set(), set()
    def add_match(score_tuple):
        cls_a, cls_b = score_tuple[5], score_tuple[6]
        if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
            matched_pairs.append(score_tuple)
            matched_a_ids.add(cls_a.id)
            matched_b_ids.add(cls_b.id)
    for st in all_scores:
        if st[5].name == st[6].name: add_match(st)
    for st in all_scores:
        if st[1] >= 0.95: add_match(st)
    for st in all_scores:
        if st[0] >= threshold: add_match(st)
    unmatched_a = [cls for cls in classes_a if cls.id not in matched_a_ids]
    unmatched_b = [cls for cls in classes_b if cls.id not in matched_b_ids]
    matched_pairs.sort(key=lambda x: x[0], reverse=True)
    return matched_pairs, unmatched_a, unmatched_b, all_scores

# --- 属性マージと関連マージの関数 (変更なし) ---
def merge_attributes_with_ai(attrs_a, attrs_b, calculator, perfect_match_threshold=0.98):
    merged_attrs, matched_b_indices = [], set()
    merged_attrs.extend(attrs_a)
    for i, attr_a in enumerate(attrs_a):
        for j, attr_b in enumerate(attrs_b):
            if j in matched_b_indices: continue
            if calculator.get_similarity(attr_a, attr_b) >= perfect_match_threshold:
                matched_b_indices.add(j)
                break
    for j, attr_b in enumerate(attrs_b):
        if j not in matched_b_indices: merged_attrs.append(attr_b)
    return sorted(list(set(merged_attrs)))

def parse_multiplicity(multi_str):
    if multi_str is None or multi_str.lower() == 'none' or not multi_str: return (1, 1)
    if multi_str == '*': return (0, float('inf'))
    if '..' in multi_str:
        low, high = multi_str.split('..')
        low = int(low) if low.isdigit() else 0
        high = float('inf') if high == '*' else int(high)
        return (low, high)
    if multi_str.isdigit():
        val = int(multi_str)
        return (val, val)
    return (1, 1)

def merge_multiplicity(multi_a, multi_b):
    low_a, high_a = parse_multiplicity(multi_a)
    low_b, high_b = parse_multiplicity(multi_b)
    merged_low, merged_high = min(low_a, low_b), max(high_a, high_b)
    if merged_low == merged_high: return str(int(merged_low))
    high_str = '*' if merged_high == float('inf') else str(int(merged_high))
    return f"{int(merged_low)}..{high_str}"

def adjust_layout_with_repulsion(classes, k_repulsion=20000, iterations=100):
    for _ in range(iterations):
        for i, cls_i in enumerate(classes):
            net_force_x, net_force_y = 0.0, 0.0
            for j, cls_j in enumerate(classes):
                if i == j: continue
                dx, dy = cls_i.x - cls_j.x, cls_i.y - cls_j.y
                distance_sq = dx**2 + dy**2
                if distance_sq < 1: distance_sq = 1
                force = k_repulsion / distance_sq
                net_force_x += force * dx / math.sqrt(distance_sq)
                net_force_y += force * dy / math.sqrt(distance_sq)
            cls_i.x += int(net_force_x / 10)
            cls_i.y += int(net_force_y / 10)
    return classes

# ▼▼▼ ID割り当てロジックを修正したマージ関数 ▼▼▼
def merge_uml_data(matches, unmatched_a, unmatched_b, data_a, data_b, calculator):
    merged_classes, id_map_a, id_map_b = [], {}, {}
    # 共有のIDカウンターを0で初期化
    new_id_counter = 0

    # 1. クラスのマージ
    for _, _, _, _, _, cls_a, cls_b in matches:
        merged_attrs = merge_attributes_with_ai(cls_a.attributes, cls_b.attributes, calculator)
        merged_name = cls_a.name if cls_a.name == cls_b.name else f"{cls_a.name}/{cls_b.name}"
        merged_x, merged_y = (cls_a.x + cls_b.x) // 2, (cls_a.y + cls_b.y) // 2
        
        # 共有カウンターからIDを割り当て
        new_class = UmlClass(str(new_id_counter), merged_name, merged_attrs, merged_x, merged_y)
        new_id_counter += 1

        merged_classes.append(new_class)
        id_map_a[cls_a.id], id_map_b[cls_b.id] = new_class.id, new_class.id
        
    # 未マッチクラスの追加
    for cls_list, id_map in [(unmatched_a, id_map_a), (unmatched_b, id_map_b)]:
        for cls in cls_list:
            # 共有カウンターからIDを割り当て
            new_class = UmlClass(str(new_id_counter), cls.name, cls.attributes, cls.x, cls.y)
            new_id_counter += 1
            
            merged_classes.append(new_class)
            id_map[cls.id] = new_class.id
            
    # 2. 関連のマージ
    merged_relations, processed_relations = [], {}
    all_relations = data_a["relations"] + data_b["relations"]
    for rel in all_relations:
        id_map = id_map_a if rel in data_a["relations"] else id_map_b
        new_source_id, new_target_id = id_map.get(rel.source_id), id_map.get(rel.target_id)
        if not (new_source_id and new_target_id): continue
        rel_key = tuple(sorted((new_source_id, new_target_id))) + (rel.type,)
        if rel_key in processed_relations:
            existing_rel = processed_relations[rel_key]
            existing_rel.source_multiplicity = merge_multiplicity(
                existing_rel.source_multiplicity, rel.source_multiplicity)
            existing_rel.target_multiplicity = merge_multiplicity(
                existing_rel.target_multiplicity, rel.target_multiplicity)
        else:
            # 共有カウンターからIDを割り当て
            new_relation = UmlRelation(str(new_id_counter),
                                       new_source_id, new_target_id, rel.type,
                                       rel.source_multiplicity, rel.target_multiplicity)
            new_id_counter += 1
            
            merged_relations.append(new_relation)
            processed_relations[rel_key] = new_relation
    
    merged_classes = adjust_layout_with_repulsion(merged_classes)
    return {"classes": merged_classes, "relations": merged_relations}
# ▲▲▲ 修正箇所ここまで ▲▲▲

# --- 実行部分 (変更なし) ---
def main():
    data_a, data_b = parse_uml_file("dataA.txt"), parse_uml_file("dataB.txt")
    if not (data_a and data_b): return
    calculator = SimilarityCalculator()
    if not calculator.model: return
    matches, unmatched_a, unmatched_b, all_scores = find_best_matches(data_a, data_b, calculator)
    
    print("\n--- 全てのクラスペアの類似度スコア一覧 ---")
    print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<25}{'Class B':<25}")
    print("-" * 85)
    for score, sem, _, stru, spa, cls_a, cls_b in all_scores:
        print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<25}{cls_b.name:<25}")

    print("\n--- 統合スコアに基づくマッチング候補 ---")
    if matches:
        print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<25}{'Class B':<25}")
        print("-" * 85)
        for score, sem, _, stru, spa, cls_a, cls_b in matches:
            print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<25}{cls_b.name:<25}")
    else:
        print("基準を超えるマッチング候補は見つかりませんでした。")

    print("\n" + "="*40)
    print("--- マッチングしたクラスの属性類似度詳細 ---")
    print("="*40)
    if not matches:
        print("マッチングされたクラスがありません。")
    else:
        for score_tuple in matches:
            cls_a, cls_b = score_tuple[5], score_tuple[6]
            print(f"\n▼ クラスペア: '{cls_a.name}' (A) vs '{cls_b.name}' (B)")
            print("-" * 40)
            attrs_a, attrs_b = cls_a.attributes, cls_b.attributes
            if not attrs_a or not attrs_b:
                print("片方または両方のクラスに属性がありません。")
                continue
            for attr_a in attrs_a:
                for attr_b in attrs_b:
                    similarity = calculator.get_similarity(attr_a, attr_b)
                    print(f"  類似度 (A:'{attr_a}', B:'{attr_b}') = {similarity:.4f}")

    print("\n--- マージ処理を実行中... ---")
    merged_data = merge_uml_data(matches, unmatched_a, unmatched_b, data_a, data_b, calculator)
    output_filename = "data_merged.txt"
    write_uml_file(output_filename, merged_data)
    print(f"マージが完了し、'{output_filename}' に結果を保存しました。")

if __name__ == "__main__":
    main()