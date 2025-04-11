import os
import logging
import json
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import uuid
import tempfile
import shutil

from services.data_store import DataStore
from services.pdf_processor import PDFProcessor
from services.notebook_processor import NotebookProcessor
from services.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", str(uuid.uuid4()))

# Initialize services
data_store = DataStore()
pdf_processor = PDFProcessor()
notebook_processor = NotebookProcessor()
ollama_client = OllamaClient()

# Allowed file extensions
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_ZIP_EXTENSIONS = {'zip'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', 
                          criteria=data_store.get_criteria(),
                          submissions=data_store.get_submissions())

@app.route('/upload-criteria', methods=['POST'])
def upload_criteria():
    """Upload and process assessment criteria PDF"""
    if 'criteria_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['criteria_file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename, ALLOWED_PDF_EXTENSIONS):
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            # Extract text from PDF
            criteria_text = pdf_processor.extract_text(file_path)
            criteria_name = file.filename
            
            # Store criteria
            data_store.set_criteria({
                'name': criteria_name,
                'text': criteria_text,
                'file_path': file_path
            })
            
            flash('Criteria uploaded successfully', 'success')
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            flash(f'Error processing PDF: {str(e)}', 'danger')
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
        return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a PDF.', 'danger')
    return redirect(url_for('index'))

@app.route('/upload-submissions', methods=['POST'])
def upload_submissions():
    """Upload and process ZIP file containing notebook submissions"""
    if 'submissions_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['submissions_file']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename, ALLOWED_ZIP_EXTENSIONS):
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            # Extract ZIP file
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            # Process notebooks from ZIP
            notebooks = notebook_processor.process_zip(file_path, extract_dir)
            
            # Save to data store
            for notebook in notebooks:
                submission_id = str(uuid.uuid4())
                data_store.add_submission({
                    'id': submission_id,
                    'folder_name': notebook['folder_name'],
                    'files': notebook['files'],
                    'notebook_content': notebook['notebook_content'],
                    'feedback': '',
                    'analyzed': False
                })
            
            flash(f'Successfully processed {len(notebooks)} submissions', 'success')
        except Exception as e:
            logger.error(f"Error processing ZIP: {str(e)}")
            flash(f'Error processing ZIP: {str(e)}', 'danger')
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
        return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a ZIP file.', 'danger')
    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze_submissions():
    """Analyze all unanalyzed submissions using Ollama"""
    try:
        # Get criteria
        criteria = data_store.get_criteria()
        if not criteria:
            flash('No assessment criteria found. Please upload criteria first.', 'warning')
            return redirect(url_for('index'))
        
        # Get submissions that haven't been analyzed yet
        submissions = data_store.get_submissions()
        unanalyzed = [s for s in submissions if not s.get('analyzed', False)]
        
        if not unanalyzed:
            flash('No unanalyzed submissions found.', 'info')
            return redirect(url_for('index'))
        
        # Process each submission
        for submission in unanalyzed:
            try:
                # Prepare prompt for Ollama
                notebook_content = submission.get('notebook_content', {})
                prompt = f"""
                You are an assessment evaluator. Analyze the following Jupyter notebook content against the assessment criteria. 
                Provide constructive feedback and identify strengths and areas for improvement.
                
                ASSESSMENT CRITERIA:
                {criteria.get('text', '')}
                
                NOTEBOOK CONTENT:
                {json.dumps(notebook_content, indent=2)}
                
                Please provide a detailed evaluation focusing on:
                1. Meeting the assignment requirements
                2. Code quality and organization
                3. Documentation and comments
                4. Results and conclusions
                5. Areas for improvement
                
                FORMAT YOUR RESPONSE AS A CONCISE EVALUATION REPORT WITH ACTIONABLE FEEDBACK.
                """
                
                # Get response from Ollama
                feedback = ollama_client.generate_feedback(prompt)
                
                # Update submission with feedback
                data_store.update_submission(submission['id'], {
                    'feedback': feedback,
                    'analyzed': True
                })
                
                logger.debug(f"Analyzed submission: {submission['id']}")
            except Exception as e:
                logger.error(f"Error analyzing submission {submission['id']}: {str(e)}")
                # Continue with next submission even if one fails
        
        flash(f'Successfully analyzed {len(unanalyzed)} submissions', 'success')
    except Exception as e:
        logger.error(f"Error in analyze_submissions: {str(e)}")
        flash(f'Error analyzing submissions: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions as JSON for the table"""
    submissions = data_store.get_submissions()
    return jsonify(submissions)

@app.route('/submission/<submission_id>', methods=['PUT'])
def update_submission(submission_id):
    """Update a submission's feedback"""
    try:
        data = request.json
        feedback = data.get('feedback', '')
        
        data_store.update_submission(submission_id, {
            'feedback': feedback
        })
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating submission: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all data (for testing)"""
    try:
        data_store.clear()
        flash('All data cleared successfully', 'success')
    except Exception as e:
        flash(f'Error clearing data: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
