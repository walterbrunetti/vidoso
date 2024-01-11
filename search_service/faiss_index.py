import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from extensions import db
from models import Video

MODEL = 'bert-base-nli-mean-tokens'


def build_faiss_index():
    """Build Faiss index"""

    sentences, videos_sentences_id, ids = _get_sentences_data()

    if not sentences:
        return None, None, None

    model = SentenceTransformer(MODEL)
    sentence_embeddings = model.encode(sentences)

    d = sentence_embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index2 = faiss.IndexIDMap(index)
    index2.add_with_ids(sentence_embeddings, np.array(ids))

    return index2, sentences, videos_sentences_id


def _get_sentences_data():
    """Generate and return sentences based on data in DB"""
    videos = db.session.execute(db.select(Video))

    sentences = []
    ids = []
    videos_sentences_id = []
    index = 0
    for row in videos:
        transcription = row.Video.transcription
        trans_sentences = transcription.split('.')
        for sentence in trans_sentences:
            sentences.append(sentence)
            ids.append(index)
            videos_sentences_id.append(row.Video.id)
            index += 1

    return sentences, videos_sentences_id, ids


def generate_sentence_embedding(q):
    model = SentenceTransformer(MODEL)
    xq = model.encode([q])
    return xq
