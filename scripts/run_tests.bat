@echo off
echo "Running test suite and capturing logs to tests/PYTEST_LOG.txt"
pytest --tb=short -v > tests\PYTEST_LOG.txt
echo "Done! Check tests\PYTEST_LOG.txt for results."
