.PHONY: help install install-dev test test-unit test-integration coverage lint format clean build docs

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e ".[dev]"
	pre-commit install

install-rpi:  ## Install package with Raspberry Pi dependencies
	pip install -e ".[rpi]"

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest tests/unit -v

test-integration:  ## Run integration tests only
	pytest tests/integration -v

test-not-rpi:  ## Run tests that don't require Raspberry Pi hardware
	pytest -m "not rpi"

coverage:  ## Run tests with coverage report
	pytest --cov=overmind --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

lint:  ## Run linters
	flake8 src tests
	mypy src

format:  ## Format code
	black src tests
	isort src tests

format-check:  ## Check code formatting without making changes
	black --check src tests
	isort --check src tests

pre-commit:  ## Run all pre-commit hooks
	pre-commit run --all-files

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

docs:  ## Build documentation (placeholder)
	@echo "Documentation build not yet implemented"

run:  ## Run the controller
	overmind run

monitor:  ## Run temperature monitoring
	overmind monitor

check-config:  ## Validate configuration
	overmind --check-config
