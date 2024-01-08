from celery import Celery, group, chord, chain
import requests


from transcribe_service.consumers import speech_to_text, speech_to_text_2, speech_to_text_3, transcribing_videos_is_done

celery_app = Celery('app_name', broker='redis://redis_service')

def produce_transcribe_messages():
    """
    Get all the video files to process and create a task for each of them.
    """
    url = f"http://search_service:5000/get_video_files"
    response = requests.get(url)
    result = response.json()
    files = result.get('files')
    if not files:
        print('No new files to process')
        return

    #header = group(speech_to_text.s(file) for file in files)()
    header = [chain(speech_to_text.s(file), speech_to_text_2.s(file), speech_to_text_3.s(file)) for file in files]

    result = chord(header)(transcribing_videos_is_done.s())
    result.get()


    #for file in files:
    #    celery_app.send_task('transcribe_service.consumers.speech_to_text', args=[file], kwargs={}, queue='pipeline_1')


if __name__ == '__main__':
    produce_transcribe_messages()
