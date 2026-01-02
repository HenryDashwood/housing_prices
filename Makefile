# Makefile for housing_prices project
# Uses .env file for PYTHONPATH (needed for nbdev subprocess workers)

.PHONY: preview docs export test clean help

help:
	@echo "Available commands:"
	@echo "  make preview  - Start nbdev preview server"
	@echo "  make docs     - Build documentation"
	@echo "  make export   - Export notebooks to src/"
	@echo "  make test     - Run nbdev tests"
	@echo "  make clean    - Clean generated files"

preview:
	uv run --env-file .env nbdev_preview

docs:
	uv run --env-file .env nbdev_docs

export:
	uv run --env-file .env nbdev_export && uv run ruff format

test:
	uv run --env-file .env nbdev_test

clean:
	rm -rf _proc docs/_site .quarto

