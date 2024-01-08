import celery
from celery.utils.log import get_task_logger
import moviepy.editor as mp
import speech_recognition as sr
from requests import Session
from deepmultilingualpunctuation import PunctuationModel

from transcribe_service.celery_app import celery_app


logger = get_task_logger(__name__)


class BaseTask(celery.Task):
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
def speech_to_text(self, video_file_name):
    """
    Task will raise a ValueError if max retries is reached.
    """
    # try:
    #     hit_other_service()
    #     # test failure scenarios
    #     if random.uniform(1, 5) <= 3:
    #         raise ValueError("damn it")
    # except ValueError as exc:
    #     logger.warning("Something wrong happened")
    #     raise self.retry(exc=exc)

    # try:
    #
    # except sr.UnknownValueError:
    #     print("Could not understand audio")
    #
    # except sr.RequestError as e:
    #     print("Could not request results. check your internet connection")


    logger.info(f'Received and processed: {video_file_name}')

    video = mp.VideoFileClip(f'videos/{video_file_name}')

    audio_file = video.audio
    audio_file.write_audiofile(f"audio/{video_file_name}.flac", codec="flac")

    return True


@celery_app.task(bind=True, base=BaseTask)
def speech_to_text_2(self, step_1_success, video_file_name):
    print(f'STEP 222 {video_file_name}')
    r = sr.Recognizer()

    with sr.AudioFile(f"audio/{video_file_name}.flac") as source:
        data = r.record(source)

    # Convert speech to text
    text = r.recognize_google(data)

    logger.info(f'TEXT FILE {video_file_name}: {text}')

    return text


@celery_app.task(bind=True, base=BaseTask)
def speech_to_text_3(self, text, video_file_name):
    print(f'STEP 333 {video_file_name} {text}')

    result = self.punctuation_model.restore_punctuation(text)
    logger.info(f'PUNCTUATION {video_file_name}: {result}')

    url = f"http://search_service:5000/add_video"
    data = {"transcript": result, "file_name": video_file_name}
    response = self.session.post(url, data=data)

    logger.info(response)

    return True


@celery_app.task(bind=True, base=BaseTask)
def transcribing_videos_is_done(self, results):
    url = f"http://search_service:5000/load_index"
    response = self.session.post(url, json={})

    logger.info(response)

    return True