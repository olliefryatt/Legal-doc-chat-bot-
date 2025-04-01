# AI Document Chatbot

A Flask-based chatbot that can analyze and answer questions about documents in the "Input files" folder.

## Setup Instructions

1. Open Terminal
2. Navigate to your project folder:
   ```bash
   cd /Users/oliverfryatt/Desktop/AI\ Bot
   ```
3. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate
   ```
4. Install required packages:
   ```bash
   pip install flask python-docx pandas openpyxl python-dotenv openai
   ```

## Running the Application

1. Make sure your virtual environment is activated
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your web browser and go to:
   ```
   http://localhost:8000
   ```

## Troubleshooting

If you encounter a "ModuleNotFoundError: No module named 'flask'" error:

1. Make sure you're in the virtual environment (you should see `(venv)` at the start of your terminal prompt)
2. If not, activate it:
   ```bash
   source venv/bin/activate
   ```
3. Install the required packages:
   ```bash
   pip install flask python-docx pandas openpyxl python-dotenv openai
   ```
4. Try running the application again:
   ```bash
   python app.py
   ```

## Dependencies

Required Python packages are listed in `requirements.txt`:
- Flask
- python-docx
- pandas
- openpyxl
- python-dotenv
- openai

## Note

Make sure you have your OpenAI API key set up in the `.env` file before running the application.

## Features

- Processes both Word (.docx) and Excel (.xlsx) files
- Uses advanced NLP for document understanding and question answering
- Modern, responsive web interface
- Real-time answers with source attribution
- Efficient document search using embeddings

## Usage

1. Type your question in the input field at the bottom of the chat interface.
2. Press Enter or click the Send button to submit your question.
3. The chatbot will search through the documents and provide an answer based on the relevant content.
4. The sources used to generate the answer will be listed below the response.

## Technical Details

- The application uses Flask for the backend
- Document processing is handled using python-docx and pandas
- Text embeddings are created using the SentenceTransformer model
- Question answering is powered by OpenAI's GPT model
- The frontend is built with vanilla JavaScript and CSS

## Notes

- The chatbot processes all documents when the application starts
- Large documents may take some time to process initially
- Make sure you have sufficient memory available for processing large documents 