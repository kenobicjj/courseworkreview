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
            order: [[0, 'asc']],
            columnDefs: [
                { responsivePriority: 1, targets: 0 },
                { responsivePriority: 2, targets: 4 },
                { responsivePriority: 3, targets: 2 }
            ],
            language: {
                search: "Search submissions:",
                emptyTable: "No submissions found",
                zeroRecords: "No matching submissions found"
            },
            pageLength: 10,
            lengthMenu: [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]]
        });
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

    // Tooltips initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
