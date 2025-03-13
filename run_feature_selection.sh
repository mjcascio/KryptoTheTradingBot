#!/bin/bash
#
# Run Feature Selection
#
# This script runs the feature selection process to identify the most predictive features
# for the ML model and updates the model accordingly.
#

# Set the directory to the script's location
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Parse command line arguments
METHOD="auto"
THRESHOLD=0.05
TOP_N=5

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --method)
            shift
            METHOD="$1"
            shift
            ;;
        --threshold)
            shift
            THRESHOLD="$1"
            shift
            ;;
        --top-n)
            shift
            TOP_N="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--method auto|threshold|top_n|rfecv] [--threshold VALUE] [--top-n VALUE]"
            exit 1
            ;;
    esac
done

echo "Starting feature selection process..."
echo "Method: $METHOD, Threshold: $THRESHOLD, Top N: $TOP_N"
echo "This may take some time depending on the amount of training data."

# Run feature selection
python update_ml_model.py --method "$METHOD" --threshold "$THRESHOLD" --top-n "$TOP_N"

# Check if feature selection was successful
if [ $? -eq 0 ]; then
    echo "Feature selection completed successfully!"
    echo "The ML model has been updated with the most predictive features."
    echo "Results and visualizations are available in the results/feature_selection directory."
    
    # List the results
    echo ""
    echo "Feature selection results:"
    ls -la results/feature_selection/
    
    # Show the selected features if available
    if ls models/selected_features_*.txt 1> /dev/null 2>&1; then
        echo ""
        echo "Selected features:"
        cat models/selected_features_*.txt | sort | uniq
    fi
    
    echo ""
    echo "To use the updated model, restart the ML-enhanced trading bot:"
    echo "./start_ml_bot.sh"
else
    echo "Feature selection failed. Check the logs for details."
fi 