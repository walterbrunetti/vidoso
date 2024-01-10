import math
from pathlib import Path

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
    default_retry_delay = 15  # wait for 15s before retrying

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
    logger.info(f'Extracting Audio for: {video_file_name}')
    try:
        video = mp.VideoFileClip(f'videos/{video_file_name}')
        audio_file = video.audio
        audio_file.write_audiofile(f"audio/{video_file_name}.flac", codec="flac")
        logger.info(f'Done Extracting Audio for: {video_file_name}')
        return True
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask)
def convert_speech_to_text_task(self, step_1_success, video_file_name):
    """Convert audio file into text (transcription)"""
    logger.info(f'Converting speech to text for: {video_file_name}')
    try:
        r = sr.Recognizer()

        file_stat = Path(f"audio/{video_file_name}.flac").stat()
        size_in_MB = file_stat.st_size / (1000 * 1000)

        chunks = []

        with sr.AudioFile(f"audio/{video_file_name}.flac") as audio_file:
            duration = audio_file.DURATION
            chunk_duration = 9 * duration / size_in_MB
            chunks_number = math.ceil(duration / chunk_duration)

            kwargs = {}
            if chunks_number > 1:  # chunk it if file exceeds 9MB (Google limit)
                kwargs['duration'] = int(chunk_duration)

            for i in range(chunks_number):
                data = r.record(audio_file, **kwargs)
                chunks.append(data)

        text = ''
        for chunk_audio in chunks:
            text += r.recognize_google(chunk_audio) + ' '

        logger.info(f'Done Converting speech to text for: {video_file_name}')
        return text
    except sr.UnknownValueError as e:
        logger.error(f'ERROR UnknownValueError Converting speech to text for: {video_file_name} - Google could not understand audio: {str(e)}')
    except sr.RequestError as e:
        logger.info(f'Error Converting speech to text for: {video_file_name} - Could not request results. check your internet connection')
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f'Unhandled error Converting speech to text for: {video_file_name} -  {str(e)}')


@celery_app.task(bind=True, base=BaseTask, default_retry_delay=10)
def add_transcript_punctuation_task(self, text, video_file_name):
    """
    Add punctuation to transcription text
    """
    logger.info(f'Add punctuation for: {video_file_name}')
    if text is None:
        logger.warn(f'Add punctuation - No text to punctuate: {video_file_name}')
        return
    try:
        result = self.punctuation_model.restore_punctuation(text)
        logger.info(f'Done Add punctuation for: {video_file_name}')
        return result
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask)
def add_video_transcript_task(self, text, video_file_name):
    """
    Add video with transcription into the search system
    """
    logger.info(f'Add video for: {video_file_name}')
    url = f"{celery_app.conf.SEARCH_URL}/add_video"

    if text is None:
        logger.warn(f'Add video - No text to add: {video_file_name}')
        return

    try:
        data = {"transcript": text, "file_name": video_file_name}
        response = self.session.post(url, data=data)
        logger.info(f'Done Add video for: {video_file_name}')
        return True
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask)
def transcribing_videos_is_done_task(self, results):
    """
    Let Search Service know transcribing videos is done.
    This task will be executed once speech to text process is done for all videos.
    """
    try:
        response = self.session.post(f"{celery_app.conf.SEARCH_URL}/load_index", json={})
        logger.info(response)
        return True
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(bind=True, base=BaseTask)
def on_chord_error(*args, **kwargs):
    """Even when some tasks could fail after retrying, trigger an index update"""
    logger.warn('Triggering index update but some videos were not processed')
    transcribing_videos_is_done_task.delay(None)
