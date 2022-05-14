var ctxbar = document.getElementById('barchart').getContext('2d');
var myChartbar = new Chart(ctxbar, {
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