# Testing

Pypperoni runs tests through the built-in Python test module, `unittest`.

## Usage

Tests can be ran from the command line from the root directory of the project.

For example:
```
python -m unittest discover -v -s ./tests -p "test_*.py"
```