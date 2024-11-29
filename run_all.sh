#!/bin/bash

# Run main.py
echo "Running main.py..."
python3 main.py

# Check if main.py executed successfully
if [ $? -eq 0 ]; then
    echo "main.py executed successfully."
    
    # Run benchmark.py and export results to benchmark_results.txt
    echo "Running benchmark.py..."
    python3 benchmark.py > benchmark_results.txt

    # Check if benchmark.py executed successfully
    if [ $? -eq 0 ]; then
        echo "benchmark.py executed successfully. Results saved to benchmark_results.txt."
    else
        echo "Error: benchmark.py failed to execute."
    fi
else
    echo "Error: main.py failed to execute. Skipping benchmark.py."
fi

