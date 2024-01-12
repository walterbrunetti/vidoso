from extensions import db
from models import Video


def text_search(q: str, k: int) -> list[int]:
    """Search in DB using full sentence match for now"""
    query = f'%{q}%'
    videos = db.session.execute(db.select(Video).filter(Video.transcription.ilike(query)).limit(k))
    return [row.Video.id for row in videos]


def hybrid_search(
        vector_result_ids: list[int],
        text_result_ids: list[int],
        q: str,
        app_sentences: list[str],
        app_videos_sentences_id: list[int]) -> tuple[list[str], list[int]]:
    """
    Re-rank results based on vector and text search.
    """
    k = len(vector_result_ids)
    vector_sentences = []
    vector_sentences_video_id = []
    for sentence_id in vector_result_ids:
        vector_sentences.append(app_sentences[sentence_id])
        vector_sentences_video_id.append(app_videos_sentences_id[sentence_id])

    if not text_result_ids:
        return vector_sentences, vector_sentences_video_id

    ranked_sentences = []
    ranked_video_ids = []
    for video_id in text_result_ids:  # prioritize exact match
        ranked_sentences.append(q)
        ranked_video_ids.append(video_id)

    items_left = k - len(ranked_sentences)
    if not items_left:
        return ranked_sentences, ranked_video_ids

    # complete results with vector search results
    for i in range(k):
        video_id = vector_sentences_video_id[i]
        sentence = vector_sentences[i]
        sentence_included = [s for s in ranked_sentences if s in sentence]

        if sentence_included:
            continue

        ranked_sentences.append(sentence)
        ranked_video_ids.append(video_id)

        items_left -= 1
        if not items_left:
            break

    return ranked_sentences, ranked_video_ids
