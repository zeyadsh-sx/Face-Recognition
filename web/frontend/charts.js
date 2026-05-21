// Chart.js configuration and initialization

const chartColors = {
    primary: '#7f22fe',
    secondary: '#155dfc',
    success: '#10b981',
    danger: '#e7000b',
    warning: '#ffb900',
    info: '#06b6d4',
    happy: '#fbbf24',
    sad: '#3b82f6',
    neutral: '#8b5cf6',
    surprised: '#ec4899',
    angry: '#ef4444',
    fearful: '#6366f1'
};

const emotionColors = {
    happy: chartColors.happy,
    sad: chartColors.sad,
    neutral: chartColors.neutral,
    surprised: chartColors.surprised,
    angry: chartColors.angry,
    fearful: chartColors.fearful
};

let charts = {};

// Daily Attendance Chart (Last 7 Days)
async function initDailyAttendanceChart() {
    try {
        const response = await fetch('/api/attendance/daily');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error fetching daily data:', data.error);
            return;
        }
        
        const ctx = document.getElementById('dailyAttendanceChart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (charts.dailyAttendance) {
            charts.dailyAttendance.destroy();
        }
        
        charts.dailyAttendance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                datasets: [
                    {
                        label: 'Present Students',
                        data: data.present,
                        borderColor: chartColors.success,
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: chartColors.success,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    },
                    {
                        label: 'Total Students',
                        data: data.total,
                        borderColor: chartColors.primary,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.4,
                        pointBackgroundColor: chartColors.primary,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(127, 34, 254, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing daily attendance chart:', error);
    }
}

// Monthly Attendance Chart (Last 12 Months)
async function initMonthlyAttendanceChart() {
    try {
        const response = await fetch('/api/attendance/monthly');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error fetching monthly data:', data.error);
            return;
        }
        
        const ctx = document.getElementById('monthlyAttendanceChart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (charts.monthlyAttendance) {
            charts.monthlyAttendance.destroy();
        }
        
        charts.monthlyAttendance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.months.map(m => {
                    const [year, month] = m.split('-');
                    return new Date(year, parseInt(month) - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                }),
                datasets: [
                    {
                        label: 'Attendance Rate (%)',
                        data: data.attendance_rates,
                        borderColor: chartColors.secondary,
                        backgroundColor: 'rgba(21, 93, 252, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: chartColors.secondary,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(21, 93, 252, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            },
                            font: { size: 11 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 10 }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing monthly attendance chart:', error);
    }
}

// Emotion Distribution Pie Chart
async function initEmotionChart() {
    try {
        const response = await fetch('/api/emotions');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error fetching emotion data:', data.error);
            return;
        }
        
        if (data.emotions.length === 0) {
            console.log('No emotion data available');
            return;
        }
        
        const ctx = document.getElementById('emotionChart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (charts.emotion) {
            charts.emotion.destroy();
        }
        
        const colors = data.emotions.map(emotion => emotionColors[emotion.toLowerCase()] || chartColors.primary);
        
        charts.emotion = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.emotions.map(e => e.charAt(0).toUpperCase() + e.slice(1)),
                datasets: [
                    {
                        data: data.percentages,
                        backgroundColor: colors,
                        borderColor: '#fff',
                        borderWidth: 2,
                        hoverBorderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 12, weight: 'bold' },
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing emotion chart:', error);
    }
}

// Hourly Attendance Chart
async function initHourlyAttendanceChart() {
    try {
        const response = await fetch('/api/attendance/hourly');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error fetching hourly data:', data.error);
            return;
        }
        
        const ctx = document.getElementById('hourlyAttendanceChart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (charts.hourlyAttendance) {
            charts.hourlyAttendance.destroy();
        }
        
        charts.hourlyAttendance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.hours,
                datasets: [
                    {
                        label: 'Attendance Count',
                        data: data.attendance,
                        backgroundColor: [
                            chartColors.primary,
                            chartColors.secondary,
                            chartColors.success,
                            chartColors.warning,
                            chartColors.danger,
                            chartColors.info
                        ],
                        borderColor: '#fff',
                        borderWidth: 2,
                        borderRadius: 8,
                        hoverBackgroundColor: chartColors.warning
                    }
                ]
            },
            options: {
                indexAxis: 'x',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(127, 34, 254, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 10 }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing hourly attendance chart:', error);
    }
}

// Initialize all charts when page loads
function initializeAllCharts() {
    initDailyAttendanceChart();
    initMonthlyAttendanceChart();
    initEmotionChart();
    initHourlyAttendanceChart();
}

// Refresh charts
function refreshCharts() {
    console.log('Refreshing charts...');
    initializeAllCharts();
}

// Add auto-refresh every 30 seconds
setInterval(refreshCharts, 30000);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAllCharts();
});
