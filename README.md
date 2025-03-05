# Sigma Judge

A Python GUI application that automatically tests contestant solutions against predefined test cases, providing real-time feedback and scores.

## Features

- **Parallel Processing**: Optional multi-threading support to speed up evaluation
- **Advanced Settings**: Configure global defaults and problem-specific overrides
- **Results Visualization**: Color-coded results grid with detailed submission views
- **Debugging Tools**: Thread monitor and detailed debug information

## Installation

### Option 1: Download Pre-built Executable (Only for Windows)

1. Download the latest executable from the [Releases Page](https://github.com/huythedev/Sigma_Judge/releases/latest)
2. Extract the ZIP file if applicable
3. Run the executable file

No Python installation or technical knowledge required!

### Option 2: Install from Source (For developers)

1. Clone this repository:
```bash
git clone https://github.com/huythedev/Sigma_Judge.git
cd Sigma_Judge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

## Usage

1. Run the application
2. Click "Load Data" to select a contest directory
3. Configure settings if needed
4. Click "Evaluate All" to start testing

## Contest Directory Structure

The application expects the following directory structure:

```
contest_directory/
  ├── contestants/
  │     ├── contestant1/
  │     │     ├── problem1.py
  │     │     └── problem2.cpp
  │     └── contestant2/
  │           └── ...
  └── problems/
        ├── problem1/
        │     ├── test01/
        │     │     ├── problem1.INP
        │     │     └── problem1.OUT
        │     ├── test02/
        │     │     ├── problem1.INP
        │     │     └── problem1.OUT
        │     └── ...
        └── problem2/
              ├── test01/
              │     ├── problem2.INP
              │     └── problem2.OUT
              ├── test02/
              │     ├── problem2.INP
              │     └── problem2.OUT
              └── ...
```

## Supported File Types

- Python (.py)
- C++ (.cpp)
- C (.c)
- Java (.java)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
