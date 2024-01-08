# Vidoso


### TODO
- Check dockerfile and validate if cache is missing (from ...)
- renaming modules
- move configs to a file (urls, ports, etc)
- refactor: make classes more cohesive

### Commands
- docker exec -ti search_service bash
- docker cp search_service/embeddings.pkl  search_service:/app/search_service/embeddings.pkl
- Run video transcribe Job: `docker exec -ti transcribe_service sh -c 'python3 transcribe_service/producer.py'`