async function loadCombinedChart() {
    const chartCanvas = document.getElementById("combinedChart");
    const chartCanvasCopy = document.getElementById("combinedChartCopy");
    if ((!chartCanvas && !chartCanvasCopy) || typeof Chart === "undefined") return;

    const response = await fetch("/api/chart-data");
    const data = await response.json();
    const points = data.points || [];
    const labels = points.map((point) => point.label);
    const sentimentData = points.map((point) => point.sentiment);
    const priceData = points.map((point) => point.price);

    const createChartConfig = (hideAxes = false) => ({
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Sentiment",
                    data: sentimentData,
                    borderColor: "#16a34a",
                    backgroundColor: "rgba(22, 163, 74, .12)",
                    tension: 0.35,
                    fill: false,
                    yAxisID: "y",
                },
                {
                    label: "Price Index",
                    data: priceData,
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, .10)",
                    tension: 0.35,
                    fill: false,
                    yAxisID: "y1",
                },
            ],
        },
        options: {
            responsive: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "#1f2937" } },
                tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}` } },
            },
            scales: {
                y: {
                    type: "linear",
                    position: "left",
                    min: -1,
                    max: 1,
                    ticks: { color: "#64748b", display: !hideAxes },
                    grid: { display: !hideAxes },
                },
                y1: {
                    type: "linear",
                    position: "right",
                    grid: { drawOnChartArea: false, display: !hideAxes },
                    ticks: { color: "#64748b", display: !hideAxes },
                },
                x: {
                    ticks: { color: "#64748b", display: !hideAxes },
                    grid: { display: !hideAxes },
                },
            },
        },
    });

    if (chartCanvas) {
        new Chart(chartCanvas, createChartConfig());
    }
    if (chartCanvasCopy) {
        new Chart(chartCanvasCopy, createChartConfig(true));
    }
}

window.addEventListener("DOMContentLoaded", loadCombinedChart);
