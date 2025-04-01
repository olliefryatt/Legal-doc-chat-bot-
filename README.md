# Legal Document Chat Bot

A chatbot that can answer questions about legal documents using OpenAI's GPT model.

## Setup Instructions

1. Clone the repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```
   You can get an API key from [OpenAI's website](https://platform.openai.com/api-keys)

4. Place your documents in the `Inputs files` directory

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to `http://localhost:8000`

## Features

- Upload and process Word documents
- Ask questions about the documents
- Get AI-powered responses based on document content
- Modern, clean user interface
- Pre-loaded suggested questions

## Security Note

The `.env` file containing your API key is not included in the repository for security reasons. Make sure to create your own `.env` file with your API key before running the application.

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