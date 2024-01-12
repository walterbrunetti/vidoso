
from config_test import app, client
from search_engine import hybrid_search


def test_hybrid_search_combines_both_search_in_results(app):
    q = "Sentence 1"
    app_sentences = [
        "Sentence 1",
        "Sentence 2",
        "Sentence 3",
        "Sentence 4",
        "Sentence 5",
    ]
    app_videos_sentences_id = [
        1,2,3,4,5
    ]
    vector_result_ids = [
        0, 4, 2
    ]
    text_result_ids = [1]

    expected_sentences = ["Sentence 1", "Sentence 5", "Sentence 3"]
    expected_video_ids = [1, 5, 3]

    sentences, video_ids = hybrid_search(vector_result_ids, text_result_ids, q, app_sentences, app_videos_sentences_id)

    assert sentences == expected_sentences
    assert video_ids == expected_video_ids

def test_hybrid_search_prioritize_text_search(app):
    q = "Sentence 1"
    app_sentences = [
        "Sentence 1",
        "Sentence 2",
        "Sentence 3",
        "Sentence 4",
        "Sentence 5",
    ]
    app_videos_sentences_id = [
        1,2,3,4,5
    ]
    vector_result_ids = [
        4, 2, 3
    ]
    text_result_ids = [1]

    expected_sentences = ["Sentence 1", "Sentence 5", "Sentence 3"]
    expected_video_ids = [1, 5, 3]

    sentences, video_ids = hybrid_search(vector_result_ids, text_result_ids, q, app_sentences, app_videos_sentences_id)

    assert sentences == expected_sentences
    assert video_ids == expected_video_ids

def test_hybrid_search_returns_vector_results_if_text_result_is_empty():
    q = "Sentence 1"
    app_sentences = [
        "Sentence 1",
        "Sentence 2",
        "Sentence 3",
        "Sentence 4",
        "Sentence 5",
    ]
    app_videos_sentences_id = [
        1, 1, 2, 2, 3
    ]
    vector_result_ids = [
        0, 4, 2
    ]
    text_result_ids = []

    expected_sentences = ["Sentence 1", "Sentence 5", "Sentence 3"]
    expected_video_ids = [1, 3, 2]

    sentences, video_ids = hybrid_search(vector_result_ids, text_result_ids, q, app_sentences, app_videos_sentences_id)

    assert sentences == expected_sentences
    assert video_ids == expected_video_ids

def test_hybrid_search_returns_text_results_only_if_found_video_sentences_are_equal_to_k():
    q = "Sentence 1"
    app_sentences = [
        "Sentence 1",
        "Sentence 2",
        "Sentence 1",
        "Sentence 4",
        "Sentence 5",
    ]
    app_videos_sentences_id = [
        1, 1, 2, 2, 3
    ]
    vector_result_ids = [
        4, 2
    ]  # k=2
    text_result_ids = [3,2]

    expected_sentences = ["Sentence 1", "Sentence 1", ]  # same sentence in 2 different videos
    expected_video_ids = [3, 2]

    sentences, video_ids = hybrid_search(vector_result_ids, text_result_ids, q, app_sentences, app_videos_sentences_id)

    assert sentences == expected_sentences
    assert video_ids == expected_video_ids
