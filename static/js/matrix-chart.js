// Matrix plugin for Chart.js
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(require('chart.js')) :
    typeof define === 'function' && define.amd ? define(['chart.js'], factory) :
    (global = global || self, factory(global.Chart));
}(this, (function (Chart) { 'use strict';
    
    Chart = Chart && Object.prototype.hasOwnProperty.call(Chart, 'default') ? Chart['default'] : Chart;
    
    function interpolateColor(color1, color2, factor) {
        if (factor === 0) {
            return color1;
        }
        if (factor === 1) {
            return color2;
        }
        
        const result = color1.slice();
        for (let i = 0; i < 3; i++) {
            result[i] = Math.round(result[i] + factor * (color2[i] - color1[i]));
        }
        return result;
    }
    
    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? [
            parseInt(result[1], 16),
            parseInt(result[2], 16),
            parseInt(result[3], 16)
        ] : [0, 0, 0];
    }
    
    function getColor(value, colors, values) {
        // Find segment
        let i = 0;
        for (; i < values.length; i++) {
            if (value <= values[i]) {
                break;
            }
        }
        
        if (i === 0) {
            return hexToRgb(colors[0]);
        }
        
        if (i === values.length) {
            return hexToRgb(colors[colors.length - 1]);
        }
        
        // Interpolate colors
        const color1 = hexToRgb(colors[i - 1]);
        const color2 = hexToRgb(colors[i]);
        
        const segmentLength = values[i] - values[i - 1];
        const factorInSegment = (value - values[i - 1]) / segmentLength;
        
        return interpolateColor(color1, color2, factorInSegment);
    }
    
    // Matrix chart type
    Chart.controllers.matrix = Chart.controllers.scatter.extend({
        dataElementType: Chart.elements.Rectangle,
        
        update: function(reset) {
            const me = this;
            const meta = me.getMeta();
            const dataset = me.getDataset();
            
            // Update rectangles
            meta.data.forEach(function(rectangle, index) {
                const xScale = me.getScaleForId(meta.xAxisID);
                const yScale = me.getScaleForId(meta.yAxisID);
                
                const index2d = {
                    row: Math.floor(index / dataset.data[0].length),
                    col: index % dataset.data[0].length
                };
                
                const value = dataset.data[index2d.row][index2d.col];
                
                // Get cell dimensions
                const width = xScale.getPixelForTick(1) - xScale.getPixelForTick(0);
                const height = yScale.getPixelForTick(1) - yScale.getPixelForTick(0);
                
                // Position the rectangle
                rectangle._xScale = xScale;
                rectangle._yScale = yScale;
                rectangle._datasetIndex = me.index;
                rectangle._index = index;
                
                // Set rectangle properties
                const x = xScale.getPixelForValue(index2d.col);
                const y = yScale.getPixelForValue(index2d.row);
                
                const gradient = dataset.backgroundColorGradient || {
                    colors: ['#4e73df', '#ffffff', '#e74a3b'],
                    values: [-1, 0, 1]
                };
                
                const rgb = getColor(value, gradient.colors, gradient.values);
                const backgroundColor = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
                
                rectangle._model = {
                    x: x,
                    y: y,
                    width: width * 0.9,
                    height: height * 0.9,
                    backgroundColor: backgroundColor,
                    borderColor: backgroundColor,
                    borderWidth: 1,
                    value: value
                };
                
                rectangle.pivot();
            });
            
            // Update tooltip
            meta.dataset._model = {
                datasetLabel: dataset.label || ''
            };
        },
        
        draw: function() {
            const meta = this.getMeta();
            const dataset = this.getDataset();
            
            meta.data.forEach(function(rectangle) {
                rectangle.draw();
            });
        }
    });
    
    // Matrix chart type definition
    Chart.defaults.matrix = {
        hover: {
            mode: 'nearest',
            intersect: true
        },
        tooltips: {
            mode: 'nearest',
            intersect: true,
            callbacks: {
                title: function() {
                    return '';
                },
                label: function(tooltipItem, data) {
                    const dataset = data.datasets[tooltipItem.datasetIndex];
                    const value = dataset.data[Math.floor(tooltipItem.index / dataset.data[0].length)][tooltipItem.index % dataset.data[0].length];
                    return `Value: ${value.toFixed(2)}`;
                }
            }
        },
        scales: {
            xAxes: [{
                type: 'category',
                offset: true,
                gridLines: {
                    offsetGridLines: true
                }
            }],
            yAxes: [{
                type: 'category',
                offset: true,
                gridLines: {
                    offsetGridLines: true
                }
            }]
        }
    };
    
}))); 