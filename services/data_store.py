import threading

class DataStore:
    """
    In-memory data store for the application.
    This class provides methods to store and retrieve assessment criteria and submissions.
    """
    
    def __init__(self):
        """Initialize the data store with empty structures."""
        self.criteria = None
        self.submissions = []
        self.lock = threading.Lock()  # For thread safety
    
    def set_criteria(self, criteria):
        """
        Set the assessment criteria.
        
        Args:
            criteria (dict): Dictionary containing criteria details.
        """
        with self.lock:
            self.criteria = criteria
    
    def get_criteria(self):
        """
        Get the current assessment criteria.
        
        Returns:
            dict: The current criteria or None if not set.
        """
        with self.lock:
            return self.criteria
    
    def add_submission(self, submission):
        """
        Add a new submission to the store.
        
        Args:
            submission (dict): Dictionary containing submission details.
        """
        with self.lock:
            self.submissions.append(submission)
    
    def get_submissions(self):
        """
        Get all submissions.
        
        Returns:
            list: List of all submissions.
        """
        with self.lock:
            return self.submissions.copy()
    
    def get_submission(self, submission_id):
        """
        Get a specific submission by ID.
        
        Args:
            submission_id (str): The ID of the submission to retrieve.
            
        Returns:
            dict: The submission with the given ID, or None if not found.
        """
        with self.lock:
            for submission in self.submissions:
                if submission['id'] == submission_id:
                    return submission.copy()
            return None
    
    def update_submission(self, submission_id, updates):
        """
        Update a submission with new values.
        
        Args:
            submission_id (str): The ID of the submission to update.
            updates (dict): Dictionary of fields to update.
            
        Returns:
            bool: True if the submission was updated, False otherwise.
        """
        with self.lock:
            for i, submission in enumerate(self.submissions):
                if submission['id'] == submission_id:
                    self.submissions[i].update(updates)
                    return True
            return False
    
    def clear(self):
        """Clear all data from the store."""
        with self.lock:
            self.criteria = None
            self.submissions = []
