up:
	docker compose up --build -d

down:
	docker compose down -v

test:
	cd backend && pytest -q ../tests ../backend/tests

lint:
	cd backend && ruff check .

seed:
	curl -s http://localhost:8080/api/v1/demo/seed -X POST -H 'X-Role: sre' | cat
