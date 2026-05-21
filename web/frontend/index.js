function refreshCharts() {
    const refreshButton = document.querySelector('.btn-refresh-charts');
    if (refreshButton) {
        if (!refreshButton.dataset.originalHtml) {
            refreshButton.dataset.originalHtml = refreshButton.innerHTML;
        }
        refreshButton.disabled = true;
        refreshButton.innerHTML = 'Refreshing...';
    }

    if (typeof initializeAllCharts === 'function') {
        initializeAllCharts();
    } else {
        console.warn('initializeAllCharts() is not defined yet.');
    }

    setTimeout(() => {
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.innerHTML = refreshButton.dataset.originalHtml;
        }
    }, 800);
}

document.addEventListener('DOMContentLoaded', function () {
    if (typeof initializeAllCharts === 'function') {
        initializeAllCharts();
    }
});
