
from main import create_app, db
from models import Video
from config_test import app, client


def test_add_video_creates_video_if_it_does_not_exist(app, client):
    with app.app_context():
        file_name = "test"
        transcription = 'some transcription'

        video = db.session.execute(db.select(Video).filter_by(file_name=file_name)).first()
        assert video is None

        res = client.post(f'/add_video', data={"file_name":file_name, "transcript": transcription})
        assert res.status_code == 200

        video = db.session.execute(db.select(Video).filter_by(file_name=file_name)).first()
        assert video is not None


def test_add_video_updates_video_if_it_exists(app, client):
    with app.app_context():
        file_name = "test"
        transcription = 'some transcription'

        video = db.session.execute(db.select(Video).filter_by(file_name=file_name)).first()
        assert video is None

        v = Video(title=file_name, file_name=file_name, transcription=transcription)
        db.session.add(v)
        db.session.commit()

        res = client.post(f'/add_video', data={"file_name":file_name, "transcript": "a better transcription"})
        assert res.status_code == 200

        updated_video = db.session.execute(db.select(Video).filter_by(file_name=file_name)).first()
        assert v.id == updated_video.Video.id
        assert updated_video.Video.transcription == "a better transcription"
