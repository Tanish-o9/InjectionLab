"""Tiny TF-IDF retriever (no vector DB needed; swap in chromadb/faiss if you like)."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Retriever:
    def __init__(self, docs: dict):
        self.ids = list(docs)
        self.docs = docs
        self.vec = TfidfVectorizer(stop_words="english")
        self.mat = self.vec.fit_transform([docs[i] for i in self.ids])

    def search(self, query, k=3):
        sims = cosine_similarity(self.vec.transform([query]), self.mat)[0]
        order = sims.argsort()[::-1][:k]
        return [(self.ids[i], self.docs[self.ids[i]]) for i in order]
