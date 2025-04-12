/**
 * Assessment Evaluation System - Main JavaScript
 * 
 * This file contains all the client-side functionality for the application,
 * including DataTables initialization and feedback management.
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables for submissions table
    if (document.getElementById('submissionsTable')) {
        const table = $('#submissionsTable').DataTable({
            responsive: true,
            order: [[1, 'asc']], // Sort by submission name by default
            columnDefs: [
                { orderable: false, targets: 0 }, // Checkbox column not sortable
                { responsivePriority: 1, targets: 1 }, // Submission name
                { responsivePriority: 2, targets: 7 }, // Actions column
                { responsivePriority: 3, targets: 3 }  // Status column
            ],
            language: {
                search: "Search submissions:",
                emptyTable: "No submissions found",
                zeroRecords: "No matching submissions found"
            },
            pageLength: 10,
            lengthMenu: [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]]
        });
        
        // Handle select all checkbox
        const selectAllCheckbox = document.getElementById('selectAllSubmissions');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                const isChecked = this.checked;
                document.querySelectorAll('.submission-checkbox').forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
            });
        }
        
        // Handle individual checkboxes
        document.querySelectorAll('.submission-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // Check if all checkboxes are checked
                const allChecked = Array.from(document.querySelectorAll('.submission-checkbox'))
                    .every(cb => cb.checked);
                
                // Update the "select all" checkbox
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = allChecked;
                    selectAllCheckbox.indeterminate = !allChecked && 
                        Array.from(document.querySelectorAll('.submission-checkbox'))
                            .some(cb => cb.checked);
                }
                
                // Update analysis button text with count
                updateAnalysisButtonText();
            });
        });
        
        // Function to update the analysis button text with count of selected submissions
        function updateAnalysisButtonText() {
            const analyzeBtn = document.querySelector('#analyzeForm button[type="submit"]');
            if (!analyzeBtn) return;
            
            const selectedCount = document.querySelectorAll('.submission-checkbox:checked').length;
            if (selectedCount > 0) {
                analyzeBtn.innerHTML = `<i class="fas fa-play-circle me-2"></i>Run Analysis on ${selectedCount} Selected`;
                analyzeBtn.disabled = false;
            } else {
                analyzeBtn.innerHTML = `<i class="fas fa-play-circle me-2"></i>Run Analysis on Selected`;
                analyzeBtn.disabled = true;
            }
        }
        
        // Initialize button text
        updateAnalysisButtonText();
        
        // Validate form submission
        const analyzeForm = document.getElementById('analyzeForm');
        if (analyzeForm) {
            analyzeForm.addEventListener('submit', function(e) {
                const selectedCount = document.querySelectorAll('.submission-checkbox:checked').length;
                if (selectedCount === 0) {
                    e.preventDefault();
                    alert('Please select at least one submission to analyze.');
                    return false;
                }
                return true;
            });
        }
    }

    // Feedback Modal Functionality
    const feedbackModal = document.getElementById('feedbackModal');
    if (feedbackModal) {
        const modalTitle = document.getElementById('feedbackModalTitle');
        const feedbackTextarea = document.getElementById('feedbackTextarea');
        const saveFeedbackBtn = document.getElementById('saveFeedbackBtn');
        let currentSubmissionId = null;

        // View feedback button click handler
        document.querySelectorAll('.view-feedback').forEach(button => {
            button.addEventListener('click', function() {
                // Get submission data
                currentSubmissionId = this.getAttribute('data-id');
                const folderName = this.getAttribute('data-folder');
                const feedback = this.getAttribute('data-feedback') || '';
                
                // Update modal
                modalTitle.textContent = folderName;
                feedbackTextarea.value = feedback;
            });
        });

        // Save feedback button click handler
        saveFeedbackBtn.addEventListener('click', function() {
            if (!currentSubmissionId) return;
            
            const updatedFeedback = feedbackTextarea.value;
            
            // Send update to server
            fetch(`/submission/${currentSubmissionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    feedback: updatedFeedback
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the UI
                    const row = document.querySelector(`tr[data-id="${currentSubmissionId}"]`);
                    if (row) {
                        const feedbackCell = row.querySelector('.feedback-preview');
                        if (feedbackCell) {
                            if (updatedFeedback) {
                                feedbackCell.textContent = updatedFeedback.substring(0, 50) + '...';
                                feedbackCell.classList.remove('text-muted');
                            } else {
                                feedbackCell.textContent = 'No feedback yet';
                                feedbackCell.classList.add('text-muted');
                            }
                        }
                        
                        // Update data attribute for next open
                        const viewBtn = row.querySelector('.view-feedback');
                        if (viewBtn) {
                            viewBtn.setAttribute('data-feedback', updatedFeedback);
                        }
                        
                        // Update status badge
                        const statusBadge = row.querySelector('.badge');
                        if (statusBadge && updatedFeedback) {
                            statusBadge.textContent = 'Analyzed';
                            statusBadge.classList.remove('bg-warning');
                            statusBadge.classList.add('bg-success');
                        }
                    }
                    
                    // Show success message
                    const modalBody = feedbackModal.querySelector('.modal-body');
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-success mt-3';
                    alertDiv.textContent = 'Feedback updated successfully';
                    modalBody.appendChild(alertDiv);
                    
                    // Remove alert after 3 seconds
                    setTimeout(() => {
                        alertDiv.remove();
                        // Close the modal
                        const bsModal = bootstrap.Modal.getInstance(feedbackModal);
                        bsModal.hide();
                    }, 2000);
                } else {
                    // Show error message
                    alert('Error updating feedback: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error updating feedback: ' + error.message);
            });
        });
    }

    // Check for analysis progress updates
    function checkAnalysisProgress() {
        fetch('/analysis-progress')
            .then(response => response.json())
            .then(data => {
                if (data.in_progress) {
                    // Update the status message
                    const statusSpan = document.getElementById('analysisStatus');
                    if (statusSpan) {
                        statusSpan.textContent = `Processing ${data.current} of ${data.total} submissions...`;
                    }
                    
                    // Check again in 2 seconds
                    setTimeout(checkAnalysisProgress, 2000);
                } else if (statusSpan) {
                    statusSpan.textContent = 'Select submissions to analyze from the table.';
                }
            })
            .catch(error => console.error('Error checking progress:', error));
    }
    
    // Start checking for progress if we're on the main page
    if (document.getElementById('analysisStatus')) {
        checkAnalysisProgress();
    }

    // Tooltips initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
