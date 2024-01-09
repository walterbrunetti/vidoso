# Vidoso




### Commands
- docker exec -ti search_service bash
- docker cp search_service/embeddings.pkl  search_service:/app/search_service/embeddings.pkl
- Run video transcribe Job: `docker exec -ti transcribe_service sh -c 'python3 transcribe_service/producer.py'`