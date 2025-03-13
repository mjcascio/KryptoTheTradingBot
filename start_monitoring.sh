#!/bin/bash

# start_monitoring.sh - Script to start the dashboard and monitoring system

echo "===== KryptoBot Monitoring System ====="
echo "Starting dashboard and monitoring components..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH!"
    exit 1
fi

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import flask, flask_socketio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install flask flask-socketio
fi

# Create necessary directories
mkdir -p logs data templates static

# Start the dashboard in the background
echo "Starting dashboard..."
python3 dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > dashboard.pid
echo "✅ Dashboard started (PID: $DASHBOARD_PID)"
echo "   Dashboard available at: http://localhost:5002"
echo ""

# Start the dashboard connector in the background
echo "Starting dashboard connector..."
python3 -c "from utils.dashboard_connector import get_connector; print('✅ Dashboard connector started')" > logs/dashboard_connector.log 2>&1 &
echo ""

# Check if the bot is running
if [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null; then
    echo "✅ Trading bot is already running (PID: $(cat bot.pid))"
else
    echo "❓ Trading bot is not running. Do you want to start a simulation for testing?"
    read -p "Start simulation? (y/n): " start_sim
    if [[ $start_sim == "y" || $start_sim == "Y" ]]; then
        echo "Starting simulation..."
        python3 test_monitoring.py -d 3600 > logs/simulation.log 2>&1 &
        SIM_PID=$!
        echo $SIM_PID > sim.pid
        echo "✅ Simulation started (PID: $SIM_PID)"
    else
        echo "ℹ️ No simulation started. You can start the bot with ./start_bot.sh"
    fi
fi

echo ""
echo "===== Monitoring Options ====="
echo "1. View real-time activity in terminal: ./live_monitor.sh"
echo "2. View dashboard in browser: http://localhost:5002"
echo "3. Stop monitoring system: ./stop_monitoring.sh"
echo ""
echo "Logs are available in the logs directory:"
echo "- Dashboard log: logs/dashboard.log"
echo "- Bot activity log: logs/trading_bot.out"
echo ""

# Create stop script
cat > stop_monitoring.sh << 'EOF'
#!/bin/bash

echo "Stopping monitoring system..."

# Stop dashboard
if [ -f "dashboard.pid" ]; then
    kill $(cat dashboard.pid) 2>/dev/null
    rm dashboard.pid
    echo "✅ Dashboard stopped"
else
    echo "ℹ️ Dashboard not running"
fi

# Stop simulation
if [ -f "sim.pid" ]; then
    kill $(cat sim.pid) 2>/dev/null
    rm sim.pid
    echo "✅ Simulation stopped"
fi

echo "Monitoring system stopped"
EOF

chmod +x stop_monitoring.sh

echo "✅ Monitoring system started successfully!" 