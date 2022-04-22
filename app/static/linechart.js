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
        responsive: true
    }
});

/*const ctx = document.getElementById('barchart').getContext('2d');
const myChart = new Chart(ctx, {
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
        responsive: true
    }
});*/