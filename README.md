# Assessment Evaluation System

An open-source assessment evaluation system using Ollama that analyzes submitted Jupyter notebooks against criteria and generates feedback.

## Features

- Upload assessment criteria PDF files
- Upload student submissions as ZIP archives containing Jupyter notebooks
- Analyze notebooks against criteria using Ollama LLM
- Review and manually edit generated feedback
- Simple and intuitive web interface

## Setup

### Prerequisites

- Python 3.6+
- [Ollama](https://github.com/ollama/ollama) - running either locally or remotely

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/assessment-evaluation-system.git
   cd assessment-evaluation-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create an `.env` file based on the example:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file to configure your environment:
   ```
   # Ollama Configuration
   OLLAMA_API_URL=http://your-ollama-url:11434
   OLLAMA_MODEL=llama2
   
   # Flask Secret Key (for sessions)
   SESSION_SECRET=your-secret-key
   ```

5. Run the application:
   ```
   python main.py
   ```

## Connecting to Your Local Ollama Instance

By default, the application tries to connect to Ollama at `http://localhost:11434`. If you're running this application on a remote server (like Replit) but want to use your local Ollama instance:

1. Run Ollama on your local machine
2. Create a secure tunnel to your local Ollama using a service like [ngrok](https://ngrok.com/):
   ```
   ngrok http 11434
   ```
3. Copy the HTTPS forwarding URL from ngrok (e.g., `https://abcd1234.ngrok.io`)
4. Set the `OLLAMA_API_URL` environment variable in your application to this URL

## License

This project is open source and available under the [MIT License](LICENSE).