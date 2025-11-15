// Color palette
const colors = {
    primary: '#0d6efd',
    success: '#198754',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#0dcaf0',
    purple: '#6f42c1',
    pink: '#d63384',
    orange: '#fd7e14',
    teal: '#20c997',
    cyan: '#0dcaf0'
};

const colorArray = [
    colors.primary,
    colors.success,
    colors.danger,
    colors.warning,
    colors.info,
    colors.purple,
    colors.pink,
    colors.orange,
    colors.teal,
    colors.cyan
];

// Chart.js default config
Chart.defaults.color = '#dee2e6';
Chart.defaults.borderColor = '#495057';

// 1. Category Pie Chart
if (document.getElementById('categoryPieChart') && spendData && spendData.length > 0) {
    const ctx = document.getElementById('categoryPieChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: spendData.map(d => d.category),
            datasets: [{
                data: spendData.map(d => d.spent),
                backgroundColor: colorArray,
                borderWidth: 2,
                borderColor: '#212529'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: { size: 12 },
                        color: '#dee2e6'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 2. Income vs Expense Bar Chart
if (document.getElementById('incomeExpenseChart')) {
    const ctx = document.getElementById('incomeExpenseChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['This Month'],
            datasets: [
                {
                    label: 'Income',
                    data: [totalIncome],
                    backgroundColor: colors.success,
                    borderWidth: 0
                },
                {
                    label: 'Expenses',
                    data: [totalSpend],
                    backgroundColor: colors.danger,
                    borderWidth: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        },
                        color: '#dee2e6'
                    },
                    grid: {
                        color: '#495057'
                    }
                },
                x: {
                    ticks: {
                        color: '#dee2e6'
                    },
                    grid: {
                        color: '#495057'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#dee2e6'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// 3. Monthly Trend Line Chart
if (document.getElementById('monthlyTrendChart') && monthlyTrends && monthlyTrends.length > 0) {
    const ctx = document.getElementById('monthlyTrendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyTrends.map(d => d.month),
            datasets: [
                {
                    label: 'Income',
                    data: monthlyTrends.map(d => d.income),
                    borderColor: colors.success,
                    backgroundColor: colors.success + '33',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2
                },
                {
                    label: 'Expenses',
                    data: monthlyTrends.map(d => d.spend),
                    borderColor: colors.danger,
                    backgroundColor: colors.danger + '33',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        },
                        color: '#dee2e6'
                    },
                    grid: {
                        color: '#495057'
                    }
                },
                x: {
                    ticks: {
                        color: '#dee2e6'
                    },
                    grid: {
                        color: '#495057'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#dee2e6'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// 4. Budget Status Chart
if (document.getElementById('budgetChart') && budgetData && budgetData.length > 0) {
    const ctx = document.getElementById('budgetChart').getContext('2d');
    
    const categories = budgetData.map(d => d.category);
    const budgetAmounts = budgetData.map(d => d.budget);
    const actualAmounts = budgetData.map(d => d.actual);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Budget',
                    data: budgetAmounts,
                    backgroundColor: colors.info,
                    borderWidth: 0
                },
                {
                    label: 'Actual',
                    data: actualAmounts,
                    backgroundColor: actualAmounts.map((actual, i) => 
                        actual > budgetAmounts[i] ? colors.danger : colors.success
                    ),
                    borderWidth: 0
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        },
                        color: '#dee2e6'
                    },
                    grid: {
                        color: '#495057'
                    }
                },
                y: {
                    ticks: {
                        color: '#dee2e6'
                    },
                    grid: {
                        color: '#495057'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#dee2e6'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.x.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}
