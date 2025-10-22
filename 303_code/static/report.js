document.addEventListener('DOMContentLoaded', function() {
  const ctx = document.getElementById('spendByCategoryChart');
  if (!ctx || typeof spendData === 'undefined' || spendData.length === 0) {
    return;
  }

  const labels = spendData.map(item => item.category);
  const data = spendData.map(item => item.spent);
  
  const backgroundColors = [
    '#0d6efd', '#6f42c1', '#d63384',
    '#dc3545', '#fd7e14', '#ffc107',
    '#198754', '#20c997', '#0dcaf0'
  ];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        label: 'Spent',
        data: data,
        backgroundColor: backgroundColors,
        borderColor: '#1e1e1e',
        borderWidth: 4,
        hoverOffset: 10,
        // This makes the doughnut ring thinner, shrinking the overall circle.
        cutout: '60%' 
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          // Keep legend at the bottom to give the chart maximum space.
          position: 'bottom', 
          labels: {
             color: '#fff'
          }
        },
        title: {
          display: false,
        }
      }
    }
  });
});

