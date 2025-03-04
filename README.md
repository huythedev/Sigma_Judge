# Sigma Judge

A Python GUI application that automatically tests contestant solutions against predefined test cases, providing real-time feedback and scores.

## Features

- **Parallel Processing**: Optional multi-threading support to speed up evaluation
- **Advanced Settings**: Configure global defaults and problem-specific overrides
- **Results Visualization**: Color-coded results grid with detailed submission views
- **Debugging Tools**: Thread monitor and detailed debug information

## Installation

1. Clone this repository:
```bash
git clone https://github.com/huythedev/Sigma_Judge.git
cd Sigma_Judge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python run.py
```

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
        │     ├── input1.txt
        │     ├── output1.txt
        │     ├── input2.txt
        │     └── output2.txt
        └── problem2/
              └── ...
```

## Supported File Types

- Python (.py)
- C++ (.cpp)
- C (.c)
- Java (.java)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
