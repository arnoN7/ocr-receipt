const ctx = document.getElementById('linechart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [{
            data: data,
            borderColor: '#FD6159',
            backgroundColor: '#FD6159'
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

const ctxbar = document.getElementById('barchart').getContext('2d');
const myChartbar = new Chart(ctxbar, {
    type: 'bar',
    data: {
        labels: labelsbar,
        datasets: [{
            data: databar,
            borderColor: '#FD6159',
            backgroundColor: '#FD6159'
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false
            }
        }
    }
});