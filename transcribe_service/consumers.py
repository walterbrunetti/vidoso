import celery
from celery.utils.log import get_task_logger
from requests import Session
import moviepy.editor as mp
import speech_recognition as sr
from deepmultilingualpunctuation import PunctuationModel

from transcribe_service.celery_app import celery_app


logger = get_task_logger(__name__)


class BaseTask(celery.Task):
    max_retries = 3
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False

    _session = None
    _punctuation_model = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """This is run by the worker when the task fails."""
        logger.error('ERROR: {0!r} failed: {1!r}'.format(task_id, exc))

    @property
    def session(self):
        if self._session is None:
            self._session = Session()
        return self._session

    @property
    def punctuation_model(self):
        if self._punctuation_model is None:
            self._punctuation_model = PunctuationModel()
        return self._punctuation_model


@celery_app.task(bind=True, base=BaseTask)
def extract_audio_task(self, video_file_name):
    """
    Task will raise a ValueError if max retries is reached.
    """
    logger.info(f'Received and processed: {video_file_name}')
    try:
        video = mp.VideoFileClip(f'videos/{video_file_name}')
        audio_file = video.audio
        audio_file.write_audiofile(f"audio/{video_file_name}.flac", codec="flac")
        return True
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask)
def convert_speech_to_text_task(self, step_1_success, video_file_name):
    """Convert audio file into text (transcription)"""
    try:
        r = sr.Recognizer()

        with sr.AudioFile(f"audio/{video_file_name}.flac") as source:
            data = r.record(source)

        # Convert speech to text
        text = r.recognize_google(data)
        logger.info(f'TEXT FILE {video_file_name}: {text}')
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        raise
    except sr.RequestError as e:
        print("Could not request results. check your internet connection")
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask, default_retry_delay=10)
def add_transcript_punctuation_task(self, text, video_file_name):
    """
    Add punctuation to transcription
    """
    try:
        result = self.punctuation_model.restore_punctuation(text)
        logger.info(f'PUNCTUATION {video_file_name}: {result}')
        return result
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask)
def add_video_transcript_task(self, text, video_file_name):
    """
    Add video with transcription into the search system
    """
    logger.info(f'STEP 333 {video_file_name} {text}')
    url = f"http://search_service:5000/add_video"

    try:
        data = {"transcript": text, "file_name": video_file_name}
        response = self.session.post(url, data=data)
        logger.info(response)
    except Exception as e:
        raise self.retry(exc=e)

    return True


@celery_app.task(bind=True, base=BaseTask)
def transcribing_videos_is_done_task(self, results):
    """
    Let Search Service know transcribing videos is done.
    This task will be executed once speech to text process is done for all videos.
    """
    url = f"http://search_service:5000/load_index"
    try:
        response = self.session.post(url, json={})
        logger.info(response)
        return True
    except Exception as e:
        raise self.retry(exc=e)
