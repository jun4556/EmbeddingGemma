# similarity_calculator.py (300mモデル版)

from sentence_transformers import SentenceTransformer, util

class SimilarityCalculator:
    """SentenceTransformerを使ってテキストの類似度を計算するクラス"""

    # ここのモデル名を'google/embeddinggemma-300m'に変更します
    def __init__(self, model_name='google/embeddinggemma-300m'):
        """
        コンストラクタ。指定されたモデルを読み込みます。
        初回実行時はモデルのダウンロードに時間がかかる場合があります。
        """
        print(f"'{model_name}' モデルを読み込んでいます...")
        try:
            self.model = SentenceTransformer(model_name)
            print("モデルの読み込みが完了しました。")
        except Exception as e:
            print(f"モデル読み込み中にエラーが発生しました: {e}")
            print("Hugging Faceへのログインが完了しているか、モデルページで利用規約に同意しているか確認してください。")
            self.model = None

    def get_similarity(self, text1, text2):
        """
        2つのテキストのコサイン類似度を計算します。
        """
        if not self.model:
            return 0.0

        embeddings = self.model.encode([text1, text2])
        score = util.cos_sim(embeddings[0], embeddings[1])[0][0]
        
        return score.item()