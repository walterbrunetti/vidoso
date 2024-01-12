from config_test import app
from main import create_app, db
from models import Video
from faiss_index import _get_sentences_data

transcription_1 = 'Sentence 1. Sentence 2. Sentence 3'
transcription_2 = 'Sentence 4. Sentence 5'

def test_get_sentences_data_creates_sentences_from_transcripts(app):
    with app.app_context():

        v = Video(title='file 1', file_name='file_1', transcription=transcription_1)
        v2 = Video(title='file 2', file_name='file_2', transcription=transcription_2)

        db.session.add(v)
        db.session.add(v2)
        db.session.commit()

        sentences, videos_sentences_id, ids = _get_sentences_data()

        expected_sentences = [
            'Sentence 1', ' Sentence 2',' Sentence 3','Sentence 4',' Sentence 5',
        ]
        expected_videos_sentences_id = [
            v.id, v.id, v.id, v2.id, v2.id
        ]
        expected_ids = [
            0, 1, 2, 3, 4,
        ]

        assert sentences == expected_sentences
        assert videos_sentences_id == expected_videos_sentences_id
        assert ids == expected_ids