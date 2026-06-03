function initChart(containerId, data, options = {}) {
    const container = document.getElementById(containerId);
    if (!container || !data || data.length === 0) return null;

    const defaultOptions = {
        width: container.clientWidth,
        height: 300,
        layout: {
            backgroundColor: '#ffffff',
            textColor: '#333333',
        },
        grid: {
            vertLines: { color: '#e5e7eb' },
            horzLines: { color: '#e5e7eb' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#e5e7eb',
        },
        timeScale: {
            borderColor: '#e5e7eb',
            timeVisible: true,
        },
    };

    const chart = LightweightCharts.createChart(container, { ...defaultOptions, ...options });

    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
    });

    const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
    });

    const chartData = data.map(d => ({
        time: d.time,
        open: parseFloat(d.open),
        high: parseFloat(d.high),
        low: parseFloat(d.low),
        close: parseFloat(d.close),
    }));

    const volumeData = data.map(d => ({
        time: d.time,
        value: parseFloat(d.volume) || 0,
        color: parseFloat(d.close) >= parseFloat(d.open) ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }));

    candlestickSeries.setData(chartData);
    volumeSeries.setData(volumeData);
    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
        if (container && chart) {
            chart.applyOptions({ width: container.clientWidth });
        }
    });
    resizeObserver.observe(container);

    return chart;
}

function changeResolution(chartInstance, chartType, resolution) {
    const buttons = document.querySelectorAll(`[data-chart="${chartType}"] button`);
    buttons.forEach(btn => {
        btn.classList.remove('bg-[#1e3a8a]', 'text-white');
        btn.classList.add('bg-gray-200');
    });
    event.target.classList.remove('bg-gray-200');
    event.target.classList.add('bg-[#1e3a8a]', 'text-white');
}

function formatNumber(num) {
    return num.toLocaleString('zh-TW');
}

function formatChange(change, percent) {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${percent.toFixed(2)}%)`;
}

window.addEventListener('DOMContentLoaded', () => {
    const chartElements = document.querySelectorAll('[data-chart]');
    chartElements.forEach(el => {
        const chartType = el.getAttribute('data-chart');
        const dataElement = el.querySelector('[data-chart-data]');
        if (dataElement && window[chartType + 'Data']) {
            initChart(el.querySelector('.chart-container').id, window[chartType + 'Data']);
        }
    });
});