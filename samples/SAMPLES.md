# Pypperoni Compiler Sample Projects

<img align="left" width="100" height="100" src="https://i.imgur.com/zSG7wSw.png" alt="Pypperoni Logo">

Pypperoni is a free and open source Python compiler and bytecode preprocessor designed and maintained by the developers of [The Legend of Pirates Online](https://tlopo.com/), a fan-made recreation of Disney's Pirates of the Caribbean Online.

Included in this repository are several samples highlighting the core elements to a Pypperoni project. You may use these samples as a base template for any project built with the Pypperoni Compiler.

## Requirements

1. Python 3.6
2. CMake < 3.5

## Setup

Before running the samples it's best to set up a virtual environment to ensure your global python is not interfering with the project requirements.

To set up the samples run the following from the root of the pypperoni project (may differ by operating system):

### Windows
```
python -m pip install venv
python -m venv .venv36
.\.venv\Scripts\activate
```

## Running
All samples are ran from within the virtual environment set up by the above commands. After running the python script, in order to generate build files it is necessary to run `cmake` against the `build` folder output.

## 00: Hello World
The first sample runs Pypperoni against a simple function declaration and subsequent call.

```
python -m samples.00-hello_world.build
```

## 01: Basic
The second sample adds in an import, and some additional branching logic.

```
python -m samples.01-basic.build
```

## 02: Exceptions
The third sample demonstrates exception handling, including raising, catching, and reraising exceptions.

```
python -m samples.02-exceptions.build
```

## 03: Async
The fourth sample demonstrates async/await functionality, including async context managers and async generators.

```
python -m samples.03-async.build
```

## 04: Threading
The fifth sample demonstrates multithreading by spawning a thread that writes random data to a file in chunks.

```
python -m samples.04-threading.build
```
