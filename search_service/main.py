from os import walk
from flask import Flask, render_template, request
from config import Config
import faiss
from sentence_transformers import SentenceTransformer
from flask_sqlalchemy import SQLAlchemy
import numpy as np

db = SQLAlchemy()


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    transcription = db.Column(db.String)
    file_name = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'{self.id} - {self.title}'




def _build_faiss_index():
    """Build Faiss index"""
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

    if not sentences:
        return None, None, None

    model = SentenceTransformer('bert-base-nli-mean-tokens')
    sentence_embeddings = model.encode(sentences)

    d = sentence_embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index2 = faiss.IndexIDMap(index)
    index2.add_with_ids(sentence_embeddings, np.array(ids))

    return index2, sentences, videos_sentences_id


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        app.index, app.sentences, app.videos_sentences_id = _build_faiss_index()

    @app.route('/')
    def home():
        return render_template(f'home.html')

    @app.route('/get_video_files', methods=['GET'])
    def get_video_files():
        """
        Get and return video files that were not processed.
        """
        filenames = next(walk("videos"), (None, None, []))[2]
        files = {file for file in filenames if file.endswith('.mp4')}

        file_names_in_db = db.session.query(Video.file_name).all()
        file_names_in_db = {row[0] for row in file_names_in_db}

        files_to_process = files - file_names_in_db

        return {"files": list(files_to_process)}

    @app.route('/search', methods=['GET'])
    def search():
        q = request.args.get('q')
        k = request.args.get('k', 5)
        if not q:
            return {"success": False, "message": "Q is missing"}

        if app.index is None:
            return {"success": False, "message": "Index is not ready"}

        sentences = app.sentences
        videos_sentences_id = app.videos_sentences_id

        model = SentenceTransformer('bert-base-nli-mean-tokens')
        xq = model.encode([q])
        D, I = app.index.search(xq, int(k))  # search

        results = []
        for i in range(int(k)):
            sentence_id = int(I[0][i])
            video_id = videos_sentences_id[sentence_id]
            video = db.session.execute(db.select(Video).filter(Video.id==video_id)).first()

            data = {
                'transcription': video.Video.transcription,
                'id': video.Video.id,
                'title': video.Video.title,
                'sentence': sentences[sentence_id]
            }
            results.append(data)

        return  {'success': True, "results": results}

    @app.route('/add_video', methods=['POST'])
    def add_video():
        file_name = request.form.get('file_name')
        transcript = request.form.get('transcript')
        title = file_name.replace('-', ' ')

        video = db.session.execute(db.select(Video).filter_by(file_name=file_name)).first()
        if video:
            db.session.query(Video).filter(Video.id == video.Video.id). \
                update({Video.transcription: transcript})
        else:
            video = Video()
            video.title = title
            video.transcription = transcript
            video.file_name = file_name
            db.session.add(video)
            db.session.commit()

        return {'success': True}

    @app.route('/load_index', methods=['POST'])
    def load_index():
        app.index, app.sentences, app.videos_sentences_id = _build_faiss_index()
        return {'success': True}

    @app.route('/healthcheck/')
    def health_check():
        return {'success': True}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)