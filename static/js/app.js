/**
 * Health Data Explorer - Main JavaScript Application
 * Provides common functionality across all pages
 */

// Global app configuration
const HealthApp = {
    // API endpoints
    endpoints: {
        prefixes: '/api/prefixes',
        categories: '/api/observations/categories',
        vitals: (category) => `/api/observations/${category}/vitals`,
        vitalData: (category, vital) => `/api/observations/${category}/${vital}/data`,
        vitalChart: (category, vital) => `/api/observations/${category}/${vital}/chart`,
        conditions: '/api/conditions',
        medications: '/api/medications',
        procedures: '/api/procedures',
        allergies: '/api/allergies'
    },
    
    // Common utilities
    utils: {
        // Format dates consistently
        formatDate: (dateString) => {
            return new Date(dateString).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        },
        
        // Format date and time
        formatDateTime: (dateString) => {
            return new Date(dateString).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        // Debounce function for search inputs
        debounce: (func, wait) => {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Show loading spinner
        showLoading: (element, message = 'Loading...') => {
            element.innerHTML = `
                <div class="d-flex justify-content-center align-items-center p-4">
                    <div class="spinner-border text-primary me-3" role="status">
                        <span class="visually-hidden">${message}</span>
                    </div>
                    <span class="text-muted">${message}</span>
                </div>
            `;
        },
        
        // Show error message
        showError: (element, message) => {
            element.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>Error:</strong> ${message}
                </div>
            `;
        },
        
        // Show empty state
        showEmpty: (element, message = 'No data available') => {
            element.innerHTML = `
                <div class="text-center p-4 text-muted">
                    <i class="bi bi-info-circle display-4 mb-3"></i>
                    <p class="mb-0">${message}</p>
                </div>
            `;
        },
        
        // Convert data to CSV
        convertToCSV: (data) => {
            if (!data || data.length === 0) return '';
            
            const headers = Object.keys(data[0]);
            const csvContent = [
                headers.join(','),
                ...data.map(row => 
                    headers.map(header => `"${(row[header] || '').toString().replace(/"/g, '""')}"`).join(',')
                )
            ].join('\n');
            
            return csvContent;
        },
        
        // Download file
        downloadFile: (content, filename, contentType = 'text/plain') => {
            const blob = new Blob([content], { type: contentType });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        },
        
        // Show toast notification
        showToast: (message, type = 'info', duration = 3000) => {
            // Create toast container if it doesn't exist
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                toastContainer.style.zIndex = '9999';
                document.body.appendChild(toastContainer);
            }
            
            // Create toast element
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;
            
            toastContainer.appendChild(toast);
            
            // Show toast
            const bsToast = new bootstrap.Toast(toast, { delay: duration });
            bsToast.show();
            
            // Remove from DOM after it's hidden
            toast.addEventListener('hidden.bs.toast', () => {
                toastContainer.removeChild(toast);
            });
        }
    },
    
    // API helper functions
    api: {
        // Generic fetch with error handling
        fetch: async (url, options = {}) => {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error(`API Error (${url}):`, error);
                throw error;
            }
        },
        
        // Get data with optional query parameters
        get: async (url, params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const fullUrl = queryString ? `${url}?${queryString}` : url;
            return HealthApp.api.fetch(fullUrl);
        }
    },
    
    // Chart utilities
    charts: {
        // Common ECharts options
        getDefaultOptions: () => ({
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(50, 50, 50, 0.9)',
                borderColor: 'transparent',
                textStyle: {
                    color: '#fff'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                axisLine: {
                    lineStyle: {
                        color: '#e9ecef'
                    }
                },
                axisLabel: {
                    color: '#6c757d'
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: '#e9ecef'
                    }
                },
                axisLabel: {
                    color: '#6c757d'
                },
                splitLine: {
                    lineStyle: {
                        color: '#f8f9fa'
                    }
                }
            },
            series: []
        }),
        
        // Create line chart
        createLineChart: (container, data, options = {}) => {
            const chart = echarts.init(container);
            const defaultOptions = HealthApp.charts.getDefaultOptions();
            
            const chartOptions = {
                ...defaultOptions,
                ...options,
                series: data.series.map(series => ({
                    ...series,
                    type: 'line',
                    smooth: true,
                    lineStyle: {
                        width: 3
                    },
                    symbolSize: 6
                }))
            };
            
            chart.setOption(chartOptions);
            
            // Make responsive
            window.addEventListener('resize', () => chart.resize());
            
            return chart;
        }
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add loading states to buttons that submit forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = `
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Loading...
                `;
                submitButton.disabled = true;
                
                // Restore button after 3 seconds (fallback)
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 3000);
            }
        });
    });
    
    // Add smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add keyboard navigation for tables
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        let currentRow = -1;
        
        table.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowDown' && currentRow < rows.length - 1) {
                currentRow++;
                rows[currentRow].focus();
                e.preventDefault();
            } else if (e.key === 'ArrowUp' && currentRow > 0) {
                currentRow--;
                rows[currentRow].focus();
                e.preventDefault();
            }
        });
        
        rows.forEach((row, index) => {
            row.addEventListener('focus', () => {
                currentRow = index;
            });
        });
    });
    
    // Global error handler for unhandled API errors
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled API error:', e.reason);
        HealthApp.utils.showToast(
            'An unexpected error occurred. Please refresh the page and try again.',
            'danger',
            5000
        );
    });
    
    // Add connection status indicator
    window.addEventListener('online', () => {
        HealthApp.utils.showToast('Connection restored', 'success', 2000);
    });
    
    window.addEventListener('offline', () => {
        HealthApp.utils.showToast('Connection lost', 'warning', 5000);
    });
    
    console.log('Health Data Explorer initialized successfully');
});

// Export for use in other scripts
window.HealthApp = HealthApp;