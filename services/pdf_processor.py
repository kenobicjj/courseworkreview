import PyPDF2
import os
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Service for processing PDF files containing assessment criteria.
    """
    
    def extract_text(self, pdf_path):
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file.
            
        Returns:
            str: Extracted text from the PDF.
            
        Raises:
            Exception: If there's an error processing the PDF.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from each page
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_criteria(self, text):
        """
        Extract structured criteria from the raw PDF text.
        This is a simple implementation that could be enhanced with NLP techniques.
        
        Args:
            text (str): Raw text extracted from the PDF.
            
        Returns:
            list: List of criteria items extracted from the text.
        """
        # Split by lines and look for numbered or bulleted items
        lines = text.split('\n')
        criteria = []
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a number or bullet (simple heuristic)
            if (line[0].isdigit() and line[1:3] in ['. ', ') ']) or line[0] in ['•', '-', '*']:
                if current_item:
                    criteria.append(current_item)
                current_item = line
            elif current_item:
                current_item += " " + line
            else:
                current_item = line
        
        # Add the last item if it exists
        if current_item:
            criteria.append(current_item)
        
        return criteria
