// Advanced Search & Filter functionality

class SearchFilter {
    constructor() {
        this.filteredRecords = [];
        this.allRecords = [];
        this.init();
    }

    init() {
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Search input
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        // Date range filter
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        if (startDateInput && endDateInput) {
            startDateInput.addEventListener('change', () => this.applyFilters(false));
            endDateInput.addEventListener('change', () => this.applyFilters(false));
        }

        // Department filter
        const departmentSelect = document.getElementById('departmentFilter');
        if (departmentSelect) {
            departmentSelect.addEventListener('change', () => this.applyFilters());
        }

        // Export buttons
        const exportCsvBtn = document.getElementById('exportCsvBtn');
        const exportJsonBtn = document.getElementById('exportJsonBtn');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportCSV());
        }
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportJSON());
        }

        // Reset button
        const resetBtn = document.getElementById('resetFiltersBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }
    }

    handleSearch(query) {
        if (!query || query.length < 2) {
            document.getElementById('searchResults').innerHTML = '';
            return;
        }

        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(async response => {
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Search failed');
                }
                return data;
            })
            .then(data => {
                this.displaySearchResults(data.results || [], query);
            })
            .catch(error => {
                console.error('Search error:', error);
                document.getElementById('searchResults').innerHTML = `<p class="text-danger">Error performing search: ${error.message}</p>`;
            });
    }

    displaySearchResults(results, query) {
        const resultsContainer = document.getElementById('searchResults');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `<p class="text-muted">No students found matching "${query}"</p>`;
            return;
        }

        let html = `<div class="search-results-list">`;
        results.forEach(item => {
            const name = item.name || item.student_name || 'Unknown';
            const subtitle = item.result_type === 'attendance'
                ? `${item.date || ''} ${item.time || ''}`.trim() || 'Attendance record'
                : item.department || item.email || item.status || item.notes || 'Student record';
            const meta = item.result_type === 'attendance'
                ? (item.emotion ? `Emotion: ${item.emotion}` : 'No emotion data')
                : '';

            html += `
                <div class="search-result-item">
                    <div class="result-info">
                        <strong>${name}</strong>
                        <small class="text-secondary d-block">${subtitle}</small>
                        ${meta ? `<small class="text-muted d-block">${meta}</small>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="searchFilter.searchByStudent('${name.replace("'", "\\'")}')">
                        View Attendance
                    </button>
                </div>
            `;
        });
        html += `</div>`;
        resultsContainer.innerHTML = html;
    }

    searchByStudent(studentName) {
        document.getElementById('studentNameFilter').value = studentName;
        this.applyFilters();
    }

    applyFilters(showAlert = true) {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const department = document.getElementById('departmentFilter').value;
        const studentName = document.getElementById('studentNameFilter').value;

        const params = new URLSearchParams({
            start_date: startDate || '',
            end_date: endDate || '',
            department: department || '',
            student_name: studentName || ''
        });

        fetch(`/api/attendance/filter?${params}`)
            .then(response => response.json())
            .then(data => {
                this.filteredRecords = data.records;
                this.displayFilteredResults(data);
            })
            .catch(error => {
                console.error('Filter error:', error);
                alert('Error applying filters');
            });
    }

    displayFilteredResults(data) {
        const resultsContainer = document.getElementById('filterResults');
        const records = data.records || [];
        const stats = data.stats || {};

        let html = `
            <div class="filter-stats">
                <div class="stat-item">
                    <h5>${stats.total_records || 0}</h5>
                    <p>Total Records</p>
                </div>
                <div class="stat-item">
                    <h5>${stats.unique_students || 0}</h5>
                    <p>Unique Students</p>
                </div>
                <div class="stat-item">
                    <p class="small">${stats.date_range || ''}</p>
                </div>
            </div>
        `;

        if (records.length === 0) {
            html += '<p class="text-muted">No records found matching the applied filters</p>';
        } else {
            html += `
                <div class="filter-results-table">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Name</th>
                                <th>Time</th>
                                <th>Emotion</th>
                                <th>Real Face</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            records.forEach(record => {
                const emotionBadge = `<span class="badge bg-info">${record.emotion}</span>`;
                const realFaceBadge = record.is_real_face ? 
                    '<span class="badge bg-success">✓</span>' : 
                    '<span class="badge bg-danger">✗</span>';
                
                html += `
                    <tr>
                        <td>${record.date}</td>
                        <td>${record.name}</td>
                        <td>${record.time}</td>
                        <td>${emotionBadge}</td>
                        <td>${realFaceBadge}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;
        }

        resultsContainer.innerHTML = html;
        this.updateExportButtons();
    }

    updateExportButtons() {
        const exportBtns = document.querySelectorAll('.export-btn');
        exportBtns.forEach(btn => {
            btn.disabled = this.filteredRecords.length === 0;
        });
    }

    async exportCSV() {
        if (this.filteredRecords.length === 0) {
            alert('No records to export');
            return;
        }

        try {
            const response = await fetch('/api/export/csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    records: this.filteredRecords,
                    filename: `attendance_${new Date().toISOString().split('T')[0]}.csv`
                })
            });

            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            this.downloadFile(blob, `attendance_${new Date().toISOString().split('T')[0]}.csv`);
        } catch (error) {
            console.error('CSV export error:', error);
            alert('Error exporting CSV');
        }
    }

    async exportJSON() {
        if (this.filteredRecords.length === 0) {
            alert('No records to export');
            return;
        }

        try {
            const response = await fetch('/api/export/json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    records: this.filteredRecords,
                    filename: `attendance_${new Date().toISOString().split('T')[0]}.json`
                })
            });

            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            this.downloadFile(blob, `attendance_${new Date().toISOString().split('T')[0]}.json`);
        } catch (error) {
            console.error('JSON export error:', error);
            alert('Error exporting JSON');
        }
    }

    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        document.getElementById('departmentFilter').value = '';
        document.getElementById('studentNameFilter').value = '';
        document.getElementById('searchResults').innerHTML = '';
        document.getElementById('filterResults').innerHTML = '';
        this.filteredRecords = [];
    }
}

// Initialize on page load
let searchFilter;
document.addEventListener('DOMContentLoaded', function() {
    searchFilter = new SearchFilter();
});
