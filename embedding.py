from sentence_transformers import SentenceTransformer

model = SentenceTransformer("google/embeddinggemma-300m")


sentences = [
    "シェフがゲストのためにおいしい食事を用意した。",
    "訪問客のために、料理人が美味しいディナーを調理した。",
    "今日の東京の天気は晴れです。",
    "今週の食料品を買いに行く必要がある。"
]


embeddings = model.encode(sentences)

similarities = model.similarity(embeddings[0], embeddings)

print("基準の文:", sentences[0])
for i in range(len(sentences)):
    print(f"「{sentences[i]}」との類似度: {similarities[0][i]:.4f}")