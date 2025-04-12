import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import uuid
import tempfile
import shutil
import glob
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", str(uuid.uuid4()))

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize uploads directory
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Import models and initialize the database
from models import db, Criteria, Submission, SubmissionFile, AnalysisSettings

# Initialize the database with the app
db.init_app(app)

# Import services (after db initialization)
from services.pdf_processor import PDFProcessor
from services.notebook_processor import NotebookProcessor
from services.ollama_client import OllamaClient

# Initialize services
pdf_processor = PDFProcessor()
notebook_processor = NotebookProcessor()
ollama_client = OllamaClient()

# Create all tables in the database
with app.app_context():
    db.create_all()
    # Create default analysis settings if they don't exist
    if not AnalysisSettings.query.first():
        default_settings = AnalysisSettings(
            preamble="You are an assessment evaluator. Analyze the following Jupyter notebook content against the assessment criteria.",
            postamble="Please provide constructive feedback that is helpful for the student's learning."
        )
        db.session.add(default_settings)
        db.session.commit()

# Allowed file extensions
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_ZIP_EXTENSIONS = {'zip'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Render the main page"""
    # Get Ollama API URL for display in the UI
    ollama_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
    
    # Get criteria, submissions, and analysis settings from database
    criteria = Criteria.query.order_by(Criteria.created_at.desc()).first()
    submissions = Submission.query.order_by(Submission.created_at.desc()).all()
    settings = AnalysisSettings.query.first()
    
    return render_template('index.html', 
                          criteria=criteria.to_dict() if criteria else None,
                          submissions=[s.to_dict() for s in submissions],
                          settings=settings.to_dict() if settings else None,
                          ollama_url=ollama_url)

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
            
            # Store criteria in database
            criteria = Criteria(
                name=criteria_name,
                text=criteria_text
            )
            db.session.add(criteria)
            db.session.commit()
            
            flash('Criteria uploaded successfully', 'success')
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            flash(f'Error processing PDF: {str(e)}', 'danger')
            db.session.rollback()
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
        
        # Create a unique directory for this upload
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the zip file
        zip_path = os.path.join(upload_dir, filename)
        file.save(zip_path)
        
        try:
            # Extract ZIP file
            extract_dir = os.path.join(upload_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            # Process notebooks from ZIP
            notebooks = notebook_processor.process_zip(zip_path, extract_dir)
            
            # Track number of added submissions
            added_count = 0
            
            # Save submissions to database
            for notebook in notebooks:
                # Create submission record
                submission = Submission(
                    folder_name=notebook['folder_name'],
                    notebook_file=next((f for f in notebook['files'] if f.endswith('.ipynb')), None),
                    file_path=os.path.join(extract_dir, notebook['folder_name']),
                    notebook_content=notebook['notebook_content'],
                    analyzed=False
                )
                db.session.add(submission)
                db.session.flush()  # Get the submission ID without committing
                
                # Add individual files
                for file_name in notebook['files']:
                    file_path = os.path.join(extract_dir, notebook['folder_name'], file_name)
                    submission_file = SubmissionFile(
                        submission_id=submission.id,
                        filename=file_name,
                        file_path=file_path
                    )
                    db.session.add(submission_file)
                
                added_count += 1
            
            # Commit all changes
            db.session.commit()
            flash(f'Successfully processed {added_count} submissions', 'success')
        except Exception as e:
            logger.error(f"Error processing ZIP: {str(e)}")
            flash(f'Error processing ZIP: {str(e)}', 'danger')
            db.session.rollback()
            # Clean up the directory on error
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
            
        return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a ZIP file.', 'danger')
    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze_submissions():
    """Analyze selected submissions using Ollama"""
    try:
        # Get criteria
        criteria = Criteria.query.order_by(Criteria.created_at.desc()).first()
        if not criteria:
            flash('No assessment criteria found. Please upload criteria first.', 'warning')
            return redirect(url_for('index'))
        
        # Get analysis settings
        settings = AnalysisSettings.query.first()
        if not settings:
            flash('Analysis settings not found. Please check your configuration.', 'warning')
            return redirect(url_for('index'))
        
        # Get selected submissions from form
        selected_ids = request.form.getlist('selected_submissions')
        if not selected_ids:
            flash('No submissions selected for analysis.', 'warning')
            return redirect(url_for('index'))
        
        # Get submissions that are selected for analysis
        submissions = Submission.query.filter(Submission.id.in_(selected_ids)).all()
        if not submissions:
            flash('No submissions found matching the selected IDs.', 'info')
            return redirect(url_for('index'))
        
        analyzed_count = 0
        total_count = len(submissions)
        
        # Process each submission
        for submission in submissions:
            try:
                # Prepare prompt for Ollama with custom preamble and postamble
                notebook_content = submission.notebook_content
                
                prompt = f"""
                {settings.preamble}
                
                ASSESSMENT CRITERIA:
                {criteria.text}
                
                NOTEBOOK CONTENT:
                {json.dumps(notebook_content, indent=2)}
                
                Please provide a detailed evaluation focusing on:
                1. Meeting the assignment requirements
                2. Code quality and organization
                3. Documentation and comments
                4. Results and conclusions
                5. Areas for improvement
                
                {settings.postamble}
                """
                
                # Get response from Ollama
                feedback = ollama_client.generate_feedback(prompt)
                
                # Update submission with feedback
                submission.feedback = feedback
                submission.analyzed = True
                submission.updated_at = datetime.utcnow()
                db.session.commit()
                
                analyzed_count += 1
                logger.debug(f"Analyzed submission: {submission.id} ({analyzed_count}/{total_count})")
                
                # Update progress in the session
                session['analysis_progress'] = {
                    'current': analyzed_count,
                    'total': total_count
                }
                
            except Exception as e:
                logger.error(f"Error analyzing submission {submission.id}: {str(e)}")
                db.session.rollback()
                # Continue with next submission even if one fails
        
        flash(f'Successfully analyzed {analyzed_count} out of {total_count} submissions', 'success')
    except Exception as e:
        logger.error(f"Error in analyze_submissions: {str(e)}")
        flash(f'Error analyzing submissions: {str(e)}', 'danger')
    
    # Clear progress from session
    session.pop('analysis_progress', None)
    return redirect(url_for('index'))

@app.route('/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions as JSON for the table"""
    submissions = Submission.query.order_by(Submission.created_at.desc()).all()
    return jsonify([s.to_dict() for s in submissions])

@app.route('/submission/<submission_id>', methods=['PUT'])
def update_submission(submission_id):
    """Update a submission's feedback"""
    try:
        data = request.json
        feedback = data.get('feedback', '')
        
        submission = Submission.query.get(submission_id)
        if not submission:
            return jsonify({'success': False, 'error': 'Submission not found'}), 404
        
        submission.feedback = feedback
        submission.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating submission: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/test-ollama', methods=['GET'])
def test_ollama():
    """Test connection to Ollama API"""
    try:
        ollama_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        logger.debug(f"Testing connection to Ollama at {ollama_url}")
        
        # Try to connect to the Ollama API
        available = ollama_client.is_available()
        
        if available:
            return jsonify({
                'status': 'success',
                'message': 'Successfully connected to Ollama API',
                'url': ollama_url
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Could not connect to Ollama API',
                'url': ollama_url
            }), 500
    except Exception as e:
        logger.error(f"Error testing Ollama: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'url': os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        }), 500

@app.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all data (for testing)"""
    try:
        # Delete all submission files to prevent orphaned data
        SubmissionFile.query.delete()
        
        # Delete all submissions
        Submission.query.delete()
        
        # Commit the changes
        db.session.commit()
        
        # Delete all files in the upload directory
        for folder in glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*')):
            if os.path.isdir(folder):
                shutil.rmtree(folder)
            else:
                os.remove(folder)
        
        flash('All submission data cleared successfully', 'success')
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        flash(f'Error clearing data: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
