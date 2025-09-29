# main.py (全面改訂版)

from file_io import parse_uml_file
from similarity_calculator import SimilarityCalculator

def find_best_matches(data_a, data_b, calculator, threshold=0.7):
    """
    (この関数は変更ありません)
    2つのクラス図データから、類似度が最も高いクラスのペアを自動で見つけ出す
    """
    classes_a = list(data_a["classes"])
    classes_b = list(data_b["classes"])
    
    all_scores = []
    for cls_a in classes_a:
        for cls_b in classes_b:
            text_a = cls_a.name + " " + " ".join(cls_a.attributes)
            text_b = cls_b.name + " " + " ".join(cls_b.attributes)
            score = calculator.get_similarity(text_a, text_b)
            
            # 閾値チェックはここで行う
            if score >= threshold:
                all_scores.append((score, cls_a, cls_b))
    
    all_scores.sort(key=lambda x: x[0], reverse=True)
    
    matched_pairs = []
    matched_a_ids = set()
    matched_b_ids = set()
    
    for score, cls_a, cls_b in all_scores:
        if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
            matched_pairs.append((score, cls_a, cls_b))
            matched_a_ids.add(cls_a.id)
            matched_b_ids.add(cls_b.id)
            
    return matched_pairs

# --- 実行部分 ---

# 1. 2つのファイルを読み込む
data_a = parse_uml_file("dataA.txt")
data_b = parse_uml_file("dataB.txt")

if data_a and data_b:
    # 2. 類似度計算機を準備
    calculator = SimilarityCalculator()

    if calculator.model:
        # 3. 全ての組み合わせの類似度を計算し、一覧表示する
        print("\n--- 全てのクラスペアの類似度スコア一覧 ---")
        all_class_scores = []
        for cls_a in data_a["classes"]:
            for cls_b in data_b["classes"]:
                text_a = cls_a.name + " " + " ".join(cls_a.attributes)
                text_b = cls_b.name + " " + " ".join(cls_b.attributes)
                score = calculator.get_similarity(text_a, text_b)
                all_class_scores.append((score, cls_a.name, cls_b.name))

        # スコアが高い順に並び替えて表示
        all_class_scores.sort(key=lambda x: x[0], reverse=True)
        for score, name_a, name_b in all_class_scores:
            print(f"スコア: {score:.4f} | '{name_a}' (A) vs '{name_b}' (B)")

        # 4. 参考情報として、閾値に基づいたマッチング候補を表示する
        print("\n--- 閾値に基づくマッチング候補 ---")
        matches = find_best_matches(data_a, data_b, calculator, threshold=0.7)
        
        if matches:
            for score, cls_a, cls_b in matches:
                print(f"スコア: {score:.4f} | '{cls_a.name}' (A) <=> '{cls_b.name}' (B)")
        else:
            print("基準を超えるマッチング候補は見つかりませんでした。")