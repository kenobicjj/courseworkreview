import os
import zipfile
import json
import nbformat
import logging
import shutil

logger = logging.getLogger(__name__)

class NotebookProcessor:
    """
    Service for processing Jupyter notebook files from ZIP archives.
    """
    
    def process_zip(self, zip_path, extract_dir):
        """
        Extract a ZIP file and process any Jupyter notebooks found.
        
        Args:
            zip_path (str): Path to the ZIP file.
            extract_dir (str): Directory to extract the ZIP contents.
            
        Returns:
            list: List of dictionaries containing notebook information.
            
        Raises:
            Exception: If there's an error processing the ZIP or notebooks.
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        try:
            # Extract the ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find all folders that contain notebook files
            notebooks = []
            
            for root, dirs, files in os.walk(extract_dir):
                ipynb_files = [f for f in files if f.endswith('.ipynb')]
                
                if not ipynb_files:
                    continue
                
                # Process each notebook in the current directory
                for ipynb_file in ipynb_files:
                    full_path = os.path.join(root, ipynb_file)
                    
                    # Get relative folder path from extract directory
                    rel_path = os.path.relpath(root, extract_dir)
                    folder_name = rel_path if rel_path != '.' else ''
                    
                    # List all files in the directory
                    all_files = os.listdir(root)
                    
                    # Extract notebook content
                    notebook_content = self.extract_notebook_content(full_path)
                    
                    notebooks.append({
                        'folder_name': folder_name or os.path.basename(ipynb_file),
                        'files': all_files,
                        'notebook_path': full_path,
                        'notebook_content': notebook_content
                    })
            
            return notebooks
        except Exception as e:
            logger.error(f"Error processing ZIP file: {str(e)}")
            raise Exception(f"Failed to process ZIP file: {str(e)}")
    
    def extract_notebook_content(self, notebook_path):
        """
        Extract content from a Jupyter notebook file.
        
        Args:
            notebook_path (str): Path to the notebook file.
            
        Returns:
            dict: Dictionary containing notebook cells and metadata.
            
        Raises:
            Exception: If there's an error processing the notebook.
        """
        try:
            # Read the notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)
            
            # Extract cells
            cells = []
            for cell in notebook.cells:
                cell_content = {
                    'cell_type': cell.cell_type,
                    'source': cell.source,
                }
                
                # If it's a code cell, include outputs
                if cell.cell_type == 'code' and hasattr(cell, 'outputs'):
                    outputs = []
                    for output in cell.outputs:
                        output_data = {'output_type': output.output_type}
                        
                        if output.output_type == 'stream':
                            output_data['text'] = output.get('text', '')
                            output_data['name'] = output.get('name', '')
                        elif output.output_type in ['display_data', 'execute_result']:
                            # Handle different data formats (text, images, etc.)
                            data = {}
                            for data_type, content in output.get('data', {}).items():
                                if data_type.startswith('text/'):
                                    data[data_type] = content
                                else:
                                    # Just note that there was binary data
                                    data[data_type] = "[binary data]"
                            output_data['data'] = data
                        
                        outputs.append(output_data)
                    
                    cell_content['outputs'] = outputs
                
                cells.append(cell_content)
            
            # Extract metadata
            metadata = {
                'kernel_spec': notebook.metadata.get('kernelspec', {}).get('name', 'unknown'),
                'language_info': notebook.metadata.get('language_info', {}).get('name', 'unknown'),
            }
            
            return {
                'cells': cells,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error extracting content from notebook: {str(e)}")
            return {
                'cells': [{'cell_type': 'markdown', 'source': f'Error processing notebook: {str(e)}'}],
                'metadata': {'error': str(e)}
            }
