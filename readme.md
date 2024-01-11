# Vidoso

## Overview


### Run the app
- Clone the repo `git clone git@github.com:walterbrunetti/vidoso.git`
- `docker-compose build && docker-compose up` - NOTE this might take several minutes on the first run.
- Open a browser tab and type `http://localhost:5000/`
- System will work with transcripts already indexed
- Optional: place MP4 videos under `videos` folder
- In a new tab in the Terminal, trigger the process to capture and index transcripts: 
  `docker exec -ti transcribe_service sh -c 'python3 transcribe_service/trigger_transcribe_process.py'`

### Troubleshooting
- If any task fails during transcribing process preventing the FAISS index to be updated, just restart the app:
`docker-compose stop && docker-compose up`.

Restarting the app will force an index update. All videos successfully transcribed will be indexed.

- URLs update (and ports)


### Limitations
- BERT 50 requests


### Architecture

