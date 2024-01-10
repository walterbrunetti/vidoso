from celery import Celery, chord, chain
import requests

from transcribe_service.consumers import \
    extract_audio_task, \
    convert_speech_to_text_task, \
    add_transcript_punctuation_task, \
    add_video_transcript_task, \
    transcribing_videos_is_done_task, on_chord_error

SEARCH_URL = 'http://search_service:5000'

def produce_transcribe_messages():
    """
    Get all the video files to process and create a task for each of them.
    """
    url = f"{SEARCH_URL}/get_video_files"
    response = requests.get(url)
    result = response.json()
    files = result.get('files')
    if not files:
        print('No new files to process')
        return

    header = [
        chain(
            extract_audio_task.s(file),
            convert_speech_to_text_task.s(file),
            add_transcript_punctuation_task.s(file),
            add_video_transcript_task.s(file)
        )
        for file in files
    ]
    result = chord(header)(transcribing_videos_is_done_task.s().on_error(on_chord_error.s()))
    result.get()

    print('Process was executed successfully')


if __name__ == '__main__':
    produce_transcribe_messages()
