from os import walk

from flask import Flask, render_template, request
from config import Config
from extensions import db
from models import Video

from faiss_index import build_faiss_index, generate_sentence_embedding
from search_engine import text_search, hybrid_search


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        app.index, app.sentences, app.videos_sentences_id = build_faiss_index()

    @app.route('/')
    def home():
        return render_template(f'home.html')

    @app.route('/get_video_files', methods=['GET'])
    def get_video_files():
        """
        Get and return video files that were not processed yet.
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
        k = int(k)
        if not q:
            return {"success": False, "message": "Q is missing"}

        if app.index is None:
            return {"success": False, "message": "Index is not ready"}

        xq = generate_sentence_embedding(q)
        D, I = app.index.search(xq, k)  # vector search
        text_search_ids = text_search(q, k)

        ranked_sentences, ranked_video_ids = hybrid_search(
            vector_result_ids=I[0],
            text_result_ids=text_search_ids,
            q=q, app_sentences=app.sentences,
            app_videos_sentences_id=app.videos_sentences_id)

        results = []
        for i in range(k):
            video_id = ranked_video_ids[i]
            video = db.session.execute(db.select(Video).filter(Video.id==video_id)).first()

            data = {
                'transcription': video.Video.transcription,
                'id': video.Video.id,
                'title': video.Video.title,
                'sentence': ranked_sentences[i]
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
        app.index, app.sentences, app.videos_sentences_id = build_faiss_index()
        return {'success': True}

    @app.route('/healthcheck/')
    def health_check():
        return {'success': True}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
