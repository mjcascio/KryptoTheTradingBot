// Global variables for charts
let sectorAllocationChart = null;
let correlationHeatmapChart = null;

// Function to update the dashboard with latest data
function updateDashboard() {
    console.log("Fetching dashboard data...");
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            console.log("Dashboard data received:", data);
            
            // Update account info
            updateAccountInfo(data.account_info);
            
            // Update positions
            updatePositions(data.positions);
            
            // Update daily stats
            updateDailyStats(data.daily_stats);
            
            // Update trade history
            updateTradeHistory(data.trade_history);
            
            // Update market status
            updateMarketStatus(data.market_status);
            
            // Update equity chart
            updateEquityChart(data.equity_history);
            
            // Update daily P/L chart
            updateDailyPLChart(data.daily_pl_history);
            
            // Update strategy performance
            updateStrategyPerformance(data.strategy_performance);
            
            // Update risk metrics
            updateRiskMetrics(data.risk_metrics);
            
            // Update ML insights
            updateMLInsights(data.ml_insights);
            
            // Update bot activity
            updateBotActivity(data.bot_activity);
            
            // Fetch and update portfolio diversification
            fetchDiversificationData();
            
            // Update last update time
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

// Function to fetch diversification data
function fetchDiversificationData() {
    fetch('/api/portfolio/diversification')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                updateDiversificationMetrics(data);
                updateSectorAllocationChart(data.current_allocation, data.recommended_allocation);
                updateCorrelationHeatmap(data.correlation_data);
                updateDiversificationRecommendations(data.recommendations);
            }
        })
        .catch(error => {
            console.error('Error fetching diversification data:', error);
        });
}

// Function to update diversification metrics
function updateDiversificationMetrics(data) {
    // Update diversification score
    const scoreElement = document.getElementById('diversification-score');
    if (scoreElement) {
        scoreElement.textContent = data.diversification_score + '/100';
        
        // Change color based on score
        if (data.diversification_score >= 70) {
            scoreElement.classList.remove('text-warning', 'text-danger');
            scoreElement.classList.add('text-success');
        } else if (data.diversification_score >= 40) {
            scoreElement.classList.remove('text-success', 'text-danger');
            scoreElement.classList.add('text-warning');
        } else {
            scoreElement.classList.remove('text-success', 'text-warning');
            scoreElement.classList.add('text-danger');
        }
    }
    
    // Update sector count
    const sectorCountElement = document.getElementById('sector-count');
    if (sectorCountElement) {
        const sectorCount = Object.keys(data.current_allocation).length;
        sectorCountElement.textContent = sectorCount + '/9';
    }
    
    // Update correlation risk
    const correlationRiskElement = document.getElementById('correlation-risk');
    if (correlationRiskElement) {
        const highCorrelationCount = data.recommendations.high_correlation_pairs.length;
        let riskLevel = 'Low';
        
        if (highCorrelationCount >= 3) {
            riskLevel = 'High';
            correlationRiskElement.classList.remove('text-success', 'text-warning');
            correlationRiskElement.classList.add('text-danger');
        } else if (highCorrelationCount >= 1) {
            riskLevel = 'Medium';
            correlationRiskElement.classList.remove('text-success', 'text-danger');
            correlationRiskElement.classList.add('text-warning');
        } else {
            correlationRiskElement.classList.remove('text-warning', 'text-danger');
            correlationRiskElement.classList.add('text-success');
        }
        
        correlationRiskElement.textContent = riskLevel;
    }
    
    // Update improvement potential
    const improvementElement = document.getElementById('improvement-potential');
    const improvementBar = document.getElementById('improvement-bar');
    
    if (improvementElement && improvementBar) {
        // Calculate improvement potential based on underweight sectors and diversification score
        const underweightCount = data.recommendations.underweight_sectors.length;
        const improvementPotential = Math.min(100, Math.max(0, 100 - data.diversification_score));
        
        let potentialText = 'Low';
        if (improvementPotential >= 60) {
            potentialText = 'High';
        } else if (improvementPotential >= 30) {
            potentialText = 'Medium';
        }
        
        improvementElement.textContent = potentialText;
        improvementBar.style.width = improvementPotential + '%';
        improvementBar.setAttribute('aria-valuenow', improvementPotential);
    }
}

// Function to update sector allocation chart
function updateSectorAllocationChart(currentAllocation, recommendedAllocation) {
    const ctx = document.getElementById('sectorAllocationChart');
    
    if (!ctx) return;
    
    // Prepare data for chart
    const sectors = Object.keys({ ...currentAllocation, ...recommendedAllocation });
    const currentData = sectors.map(sector => (currentAllocation[sector] || 0) * 100);
    const recommendedData = sectors.map(sector => (recommendedAllocation[sector] || 0) * 100);
    
    // Destroy existing chart if it exists
    if (sectorAllocationChart) {
        sectorAllocationChart.destroy();
    }
    
    // Create new chart
    sectorAllocationChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sectors,
            datasets: [
                {
                    label: 'Current Allocation (%)',
                    data: currentData,
                    backgroundColor: 'rgba(78, 115, 223, 0.7)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                    order: 2
                },
                {
                    label: 'Recommended Allocation (%)',
                    data: recommendedData,
                    backgroundColor: 'rgba(28, 200, 138, 0.7)',
                    borderColor: 'rgba(28, 200, 138, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 10,
                    right: 25,
                    bottom: 10,
                    left: 25
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 10,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Allocation (%)',
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: {top: 10, bottom: 10}
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 10,
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'center',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'rgba(255, 255, 255, 1)',
                    bodyColor: 'rgba(255, 255, 255, 1)',
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Function to update correlation heatmap
function updateCorrelationHeatmap(correlationData) {
    const ctx = document.getElementById('correlationHeatmap');
    
    if (!ctx || !correlationData.symbols || correlationData.symbols.length === 0) {
        // If no correlation data or no symbols, display a message
        if (ctx) {
            const parent = ctx.parentElement;
            if (parent) {
                parent.innerHTML = '<div class="text-center py-5">Not enough positions to calculate correlations</div>';
            }
        }
        return;
    }
    
    // Prepare data for heatmap
    const symbols = correlationData.symbols;
    const matrix = correlationData.matrix;
    
    // Create data array for heatmap
    const data = [];
    for (let i = 0; i < symbols.length; i++) {
        const row = [];
        for (let j = 0; j < symbols.length; j++) {
            row.push(matrix[symbols[i]][symbols[j]]);
        }
        data.push(row);
    }
    
    // Destroy existing chart if it exists
    if (correlationHeatmapChart) {
        correlationHeatmapChart.destroy();
    }
    
    // Create new chart
    correlationHeatmapChart = new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                label: 'Correlation Matrix',
                data: data,
                width: ({ chart }) => (chart.chartArea || {}).width / symbols.length - 1,
                height: ({ chart }) => (chart.chartArea || {}).height / symbols.length - 1,
                backgroundColorGradient: {
                    colors: ['#4e73df', '#ffffff', '#e74a3b'],
                    values: [-1, 0, 1]
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 10,
                    right: 25,
                    bottom: 10,
                    left: 25
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: symbols,
                    offset: true,
                    ticks: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 10,
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'category',
                    labels: symbols,
                    offset: true,
                    ticks: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 10
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'rgba(255, 255, 255, 1)',
                    bodyColor: 'rgba(255, 255, 255, 1)',
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function() {
                            return '';
                        },
                        label: function(context) {
                            const i = context.dataIndex % symbols.length;
                            const j = Math.floor(context.dataIndex / symbols.length);
                            return `${symbols[j]} vs ${symbols[i]}: ${context.raw.toFixed(2)}`;
                        }
                    }
                }
            }
        }
    });
}

// Function to update diversification recommendations
function updateDiversificationRecommendations(recommendations) {
    const container = document.getElementById('diversification-recommendations');
    
    if (!container) return;
    
    // Clear existing content
    container.innerHTML = '';
    
    // Add overweight sector recommendations
    recommendations.overweight_sectors.forEach(sector => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-warning">Overweight</span></td>
            <td>Your portfolio has ${(sector.current_allocation * 100).toFixed(1)}% in ${sector.sector} sector, which is ${(sector.difference * 100).toFixed(1)}% above the recommended ${(sector.recommended_allocation * 100).toFixed(1)}%.</td>
            <td><button class="btn btn-sm btn-outline-warning">Rebalance</button></td>
        `;
        container.appendChild(row);
    });
    
    // Add underweight sector recommendations
    recommendations.underweight_sectors.forEach(sector => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-info">Underweight</span></td>
            <td>Your portfolio has ${(sector.current_allocation * 100).toFixed(1)}% in ${sector.sector} sector, which is ${Math.abs(sector.difference * 100).toFixed(1)}% below the recommended ${(sector.recommended_allocation * 100).toFixed(1)}%.</td>
            <td><button class="btn btn-sm btn-outline-info">Add Position</button></td>
        `;
        container.appendChild(row);
    });
    
    // Add high correlation pair recommendations
    recommendations.high_correlation_pairs.forEach(pair => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-danger">High Correlation</span></td>
            <td>${pair.symbol1} and ${pair.symbol2} have a correlation of ${pair.correlation.toFixed(2)}, which increases portfolio risk.</td>
            <td><button class="btn btn-sm btn-outline-danger">Diversify</button></td>
        `;
        container.appendChild(row);
    });
    
    // Add suggested additions
    const suggestedAdditions = recommendations.suggested_additions.slice(0, 5); // Limit to 5 suggestions
    suggestedAdditions.forEach(suggestion => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-success">Suggestion</span></td>
            <td>Consider adding ${suggestion.symbol} to increase exposure to the ${suggestion.sector} sector.</td>
            <td><button class="btn btn-sm btn-outline-success">Analyze</button></td>
        `;
        container.appendChild(row);
    });
    
    // If no recommendations, show a message
    if (container.children.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="3" class="text-center">No diversification recommendations at this time.</td>
        `;
        container.appendChild(row);
    }
}

// Function to update account information
function updateAccountInfo(accountInfo) {
    if (!accountInfo) return;
    
    document.getElementById('equity').textContent = accountInfo.equity ? accountInfo.equity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00';
    document.getElementById('buying-power').textContent = accountInfo.buying_power ? accountInfo.buying_power.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00';
    document.getElementById('cash').textContent = accountInfo.cash ? accountInfo.cash.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00';
}

// Function to update daily statistics
function updateDailyStats(dailyStats) {
    if (!dailyStats) return;
    
    document.getElementById('total-trades').textContent = dailyStats.trades || '0';
    document.getElementById('win-rate').textContent = dailyStats.win_rate ? dailyStats.win_rate.toFixed(1) : '0.0';
    document.getElementById('total-pl').textContent = dailyStats.total_pl ? dailyStats.total_pl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00';
}

// Function to update market status
function updateMarketStatus(marketStatus) {
    if (!marketStatus) return;
    
    const statusElement = document.getElementById('market-status');
    if (marketStatus.is_open) {
        statusElement.textContent = 'OPEN';
        statusElement.className = 'market-open';
    } else {
        statusElement.textContent = 'CLOSED';
        statusElement.className = 'market-closed';
    }
    
    const nextTimeElement = document.getElementById('market-next-time');
    if (marketStatus.is_open) {
        nextTimeElement.textContent = `Closes at ${marketStatus.next_close}`;
    } else {
        nextTimeElement.textContent = `Opens at ${marketStatus.next_open}`;
    }
}

// Function to update positions
function updatePositions(positions) {
    const container = document.getElementById('positions-container');
    if (!container) return;
    
    // Clear existing positions
    container.innerHTML = '';
    
    // Check if there are any positions
    if (!positions || Object.keys(positions).length === 0) {
        container.innerHTML = '<div class="text-center py-4">No active positions</div>';
        return;
    }
    
    // Create position cards
    for (const symbol in positions) {
        const position = positions[symbol];
        const isProfit = position.unrealized_pl > 0;
        const profitLossClass = isProfit ? 'profit' : 'loss';
        
        // Calculate price range for progress bar
        const range = position.take_profit - position.stop_loss;
        const currentPosition = (position.current_price - position.stop_loss) / range * 100;
        const entryPosition = (position.entry_price - position.stop_loss) / range * 100;
        
        // Calculate profit/loss percentage
        const plPercentage = ((position.current_price - position.entry_price) / position.entry_price * 100).toFixed(2);
        
        // Create position card HTML
        const card = document.createElement('div');
        card.className = 'position-card';
        card.innerHTML = `
            <div class="card-body">
                <div class="card-title">
                    <span class="symbol-badge">${symbol}</span>
                    <span class="${profitLossClass}">$${position.unrealized_pl.toFixed(2)} (${plPercentage}%)</span>
                </div>
                <div class="position-details">
                    <div class="detail-group">
                        <div class="detail-label">Quantity</div>
                        <div class="detail-value">${position.quantity}</div>
                    </div>
                    <div class="detail-group">
                        <div class="detail-label">Entry Price</div>
                        <div class="detail-value">$${position.entry_price.toFixed(2)}</div>
                    </div>
                    <div class="detail-group">
                        <div class="detail-label">Current Price</div>
                        <div class="detail-value">$${position.current_price.toFixed(2)}</div>
                    </div>
                    <div class="detail-group">
                        <div class="detail-label">Market Value</div>
                        <div class="detail-value">$${(position.quantity * position.current_price).toFixed(2)}</div>
                    </div>
                </div>
                <div class="progress-container">
                    <div class="price-indicator" style="width: 100%;"></div>
                    <div class="price-marker" style="left: ${entryPosition}%;" title="Entry: $${position.entry_price.toFixed(2)}"></div>
                    <div class="price-marker" style="left: ${currentPosition}%;" title="Current: $${position.current_price.toFixed(2)}"></div>
                </div>
                <div class="price-labels">
                    <span>Stop Loss: $${position.stop_loss.toFixed(2)}</span>
                    <span>Take Profit: $${position.take_profit.toFixed(2)}</span>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    }
}

// Function to update equity chart
function updateEquityChart(equityHistory) {
    const ctx = document.getElementById('equity-chart');
    if (!ctx) return;
    
    // Check if we have data
    if (!equityHistory || equityHistory.length === 0) return;
    
    // Prepare data
    const labels = equityHistory.map(item => item[0]);
    const data = equityHistory.map(item => item[1]);
    
    // Create chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Equity',
                data: data,
                borderColor: 'rgba(78, 115, 223, 1)',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                pointBorderColor: '#fff',
                pointHoverRadius: 5,
                pointHoverBackgroundColor: 'rgba(78, 115, 223, 1)',
                pointHoverBorderColor: '#fff',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 5,
                    right: 15,
                    bottom: 5,
                    left: 15
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false,
                        drawTicks: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 8,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false,
                        drawTicks: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 8,
                        maxRotation: 0,
                        maxTicksLimit: 7
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'rgba(255, 255, 255, 1)',
                    bodyColor: 'rgba(255, 255, 255, 1)',
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '$' + context.raw.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Function to update daily P/L chart
function updateDailyPLChart(plHistory) {
    const ctx = document.getElementById('daily-pl-chart');
    if (!ctx) return;
    
    // Check if we have data
    if (!plHistory || plHistory.length === 0) return;
    
    // Prepare data
    const labels = plHistory.map(item => item[0]);
    const data = plHistory.map(item => item[1]);
    
    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily P/L',
                data: data,
                backgroundColor: data.map(value => value >= 0 ? 'rgba(28, 200, 138, 0.7)' : 'rgba(231, 74, 59, 0.7)'),
                borderColor: data.map(value => value >= 0 ? 'rgba(28, 200, 138, 1)' : 'rgba(231, 74, 59, 1)'),
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 10,
                    right: 25,
                    bottom: 10,
                    left: 25
                }
            },
            scales: {
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 10,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 10,
                        maxRotation: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'rgba(255, 255, 255, 1)',
                    bodyColor: 'rgba(255, 255, 255, 1)',
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '$' + context.raw.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Function to update strategy performance
function updateStrategyPerformance(strategyPerformance) {
    const tableBody = document.getElementById('strategy-performance');
    if (!tableBody) return;
    
    // Clear existing content
    tableBody.innerHTML = '';
    
    // Check if we have data
    if (!strategyPerformance) return;
    
    // Add rows for each strategy
    for (const strategy in strategyPerformance) {
        const data = strategyPerformance[strategy];
        const winRate = data.trades > 0 ? (data.wins / data.trades * 100).toFixed(1) + '%' : '0.0%';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${strategy.charAt(0).toUpperCase() + strategy.slice(1)}</td>
            <td>${data.trades}</td>
            <td>${winRate}</td>
            <td class="${data.pl >= 0 ? 'profit' : 'loss'}">$${data.pl.toFixed(2)}</td>
        `;
        
        tableBody.appendChild(row);
    }
}

// Function to update risk metrics
function updateRiskMetrics(riskMetrics) {
    if (!riskMetrics) return;
    
    // Update portfolio heat
    const heatBar = document.getElementById('portfolio-heat-bar');
    if (heatBar) {
        const heat = riskMetrics.portfolio_heat || 0;
        heatBar.style.width = heat + '%';
        heatBar.textContent = heat.toFixed(1) + '%';
        heatBar.setAttribute('aria-valuenow', heat);
        
        // Change color based on heat level
        if (heat > 50) {
            heatBar.className = 'progress-bar bg-danger';
        } else if (heat > 30) {
            heatBar.className = 'progress-bar bg-warning';
        } else {
            heatBar.className = 'progress-bar bg-success';
        }
    }
    
    // Update drawdown
    const drawdownBar = document.getElementById('drawdown-bar');
    if (drawdownBar) {
        const drawdown = riskMetrics.drawdown || 0;
        drawdownBar.style.width = drawdown + '%';
        drawdownBar.textContent = drawdown.toFixed(1) + '%';
        drawdownBar.setAttribute('aria-valuenow', drawdown);
    }
    
    // Update position diversification
    const diversificationBar = document.getElementById('diversification-bar');
    if (diversificationBar && riskMetrics.max_positions > 0) {
        const positionCount = riskMetrics.position_count || 0;
        const maxPositions = riskMetrics.max_positions || 10;
        const diversification = (positionCount / maxPositions) * 100;
        
        diversificationBar.style.width = diversification + '%';
        diversificationBar.textContent = positionCount + '/' + maxPositions;
        diversificationBar.setAttribute('aria-valuenow', diversification);
    }
    
    // Update risk metrics table
    document.getElementById('max-drawdown').textContent = (riskMetrics.max_drawdown || 0).toFixed(1) + '%';
    document.getElementById('sharpe-ratio').textContent = (riskMetrics.sharpe_ratio || 0).toFixed(2);
    document.getElementById('profit-factor').textContent = (riskMetrics.profit_factor || 0).toFixed(2);
    document.getElementById('win-loss-ratio').textContent = (riskMetrics.win_loss_ratio || 0).toFixed(2);
    document.getElementById('avg-win').textContent = '$' + (riskMetrics.avg_win || 0).toFixed(2);
    document.getElementById('avg-loss').textContent = '$' + (riskMetrics.avg_loss || 0).toFixed(2);
}

// Function to update ML insights
function updateMLInsights(mlInsights) {
    if (!mlInsights) return;
    
    // Update model performance metrics
    if (mlInsights.model_performance) {
        const performance = mlInsights.model_performance;
        document.getElementById('model-accuracy').textContent = (performance.accuracy * 100).toFixed(0) + '%';
        document.getElementById('model-precision').textContent = (performance.precision * 100).toFixed(0) + '%';
        document.getElementById('model-recall').textContent = (performance.recall * 100).toFixed(0) + '%';
        document.getElementById('model-f1').textContent = (performance.f1_score * 100).toFixed(0) + '%';
        document.getElementById('model-auc').textContent = performance.auc.toFixed(2);
    }
    
    // Update recent predictions
    const predictionsTable = document.getElementById('recent-predictions');
    if (predictionsTable && mlInsights.recent_predictions) {
        // Clear existing content
        predictionsTable.innerHTML = '';
        
        // Add rows for recent predictions
        mlInsights.recent_predictions.slice(0, 5).forEach(prediction => {
            const row = document.createElement('tr');
            const isCorrect = prediction.prediction === prediction.actual;
            
            row.innerHTML = `
                <td>${prediction.timestamp}</td>
                <td>${prediction.symbol}</td>
                <td>${prediction.prediction}</td>
                <td>${(prediction.confidence * 100).toFixed(0)}%</td>
                <td class="${isCorrect ? 'text-success' : 'text-danger'}">${prediction.actual}</td>
            `;
            
            predictionsTable.appendChild(row);
        });
    }
}

// Function to update bot activity
function updateBotActivity(botActivity) {
    // This function would update the bot activity log
    // Implementation depends on how you want to display this information
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initial update
    updateDashboard();
    
    // Set up periodic updates (every 5 seconds)
    setInterval(updateDashboard, 5000);
}); 