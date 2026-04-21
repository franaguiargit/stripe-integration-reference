.PHONY: run test webhook-forward install clean

install:
	pip install -r requirements.txt

run:
	uvicorn src.main:app --reload --port 8000

test:
	pytest -v

webhook-forward:
	stripe listen --forward-to localhost:8000/webhook

clean:
	rm -f stripe_integration.db
	find . -type d -name __pycache__ -exec rm -rf {} +
