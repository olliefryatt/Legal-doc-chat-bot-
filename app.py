import os
import sys
import json
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Print Python version and environment info
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir('.')}")

# Load environment variables from .env file
load_dotenv()

# Debug environment variables
logger.info("Environment variables:")
logger.info(f"OPENAI_API_KEY exists: {bool(os.environ.get('OPENAI_API_KEY'))}")
if os.environ.get('OPENAI_API_KEY'):
    logger.info(f"OPENAI_API_KEY length: {len(os.environ.get('OPENAI_API_KEY'))}")
logger.info(f"PORT: {os.environ.get('PORT')}")
logger.info(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client with error handling
try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    openai.api_key = api_key
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")
    # Don't raise here, let the app start anyway for troubleshooting

# Try to load documents data from JSON with robust error handling
documents_data = {'documents': {}, 'excel_data': {}}
try:
    logger.info("Attempting to load documents_data.json")
    with open('documents_data.json', 'r', encoding='utf-8') as f:
        documents_data = json.load(f)
    
    logger.info(f"Documents in JSON: {list(documents_data['documents'].keys())}")
    logger.info(f"Excel data in JSON: {list(documents_data.get('excel_data', {}).keys())}")
    logger.info("Documents data loaded successfully")
except FileNotFoundError:
    logger.error("documents_data.json file not found")
    logger.info(f"Files in directory: {os.listdir('.')}")
except json.JSONDecodeError as e:
    logger.error(f"JSON parsing error in documents_data.json: {str(e)}")
except Exception as e:
    logger.error(f"Error loading documents data: {str(e)}")

def format_content_for_context(content):
    """Format different content types into readable text."""
    try:
        if isinstance(content, list):
            return "\n".join(format_content_for_context(item) for item in content)
        
        if isinstance(content, dict):
            if content.get('type') == 'paragraph':
                return content.get('text', '')
            elif content.get('type') == 'section':
                section_text = f"\n## {content.get('title', '')}\n"
                if 'content' in content:
                    section_text += format_content_for_context(content['content'])
                return section_text
            elif content.get('type') == 'list':
                return "\n".join(f"- {item}" for item in content.get('items', []))
            elif content.get('type') == 'compliance_table':
                table_text = f"\n### {content.get('title', '')}\n"
                headers = content.get('headers', [])
                rows = content.get('rows', [])
                if headers and rows:
                    table_text += " | ".join(headers) + "\n"
                    table_text += " | ".join("-" * len(header) for header in headers) + "\n"
                    for row in rows:
                        table_text += " | ".join(str(row.get(h, '')) for h in headers) + "\n"
                return table_text
            elif content.get('type') == 'financial_table':
                table_text = f"\n### {content.get('title', '')}\n"
                years = content.get('years', [])
                data = content.get('data', {})
                if years and data:
                    table_text += " | " + " | ".join(years) + "\n"
                    table_text += " | " + " | ".join("-" * len(year) for year in years) + "\n"
                    for key, values in data.items():
                        table_text += f"{key} | " + " | ".join(str(v) for v in values) + "\n"
                return table_text
            elif content.get('type') == 'details':
                return "\n".join(f"{k}: {v}" for k, v in content.get('items', {}).items())
            elif content.get('type') == 'management_member':
                return f"{content.get('name', '')} - {content.get('position', '')}: {content.get('details', '')}"
            elif content.get('type') == 'signature_block':
                return f"\nSigned by: {content.get('name', '')}\n{content.get('title', '')}\n{content.get('company', '')}\nDate: {content.get('date', '')}"
            else:
                return str(content)
        return str(content)
    except Exception as e:
        logger.error(f"Error in format_content_for_context: {str(e)}")
        return "[Error formatting content]"

@app.route('/')
def index():
    try:
        logger.info("Rendering index.html template")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return f"Error rendering template: {str(e)}", 500

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "python_version": sys.version,
        "documents_loaded": len(documents_data.get('documents', {})),
        "openai_configured": bool(os.environ.get('OPENAI_API_KEY'))
    })

@app.route('/ask', methods=['POST'])
def ask():
    try:
        logger.info("Received /ask request")
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        question = data.get('question')
        
        if not question:
            logger.warning("No question provided in request")
            return jsonify({'error': 'No question provided'}), 400
        
        # Create context from documents data
        context = ""
        try:
            for doc_name, doc_info in documents_data['documents'].items():
                context += f"\n# Document: {doc_name}\n"
                if 'content' in doc_info:
                    context += format_content_for_context(doc_info['content'])
                context += "\n"
            
            # Add Excel data to context if available
            if 'excel_data' in documents_data:
                for excel_name, excel_info in documents_data['excel_data'].items():
                    context += f"\n# Excel Data: {excel_name}\n"
                    context += json.dumps(excel_info.get('data', {}), indent=2)
        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            context = "Error building context from documents."
        
        # Debug info
        logger.info(f"Question received: {question}")
        logger.info(f"Context length: {len(context)} characters")
        logger.info(f"Context preview (first 200 chars): {context[:200]}...")
        
        # If OpenAI is not properly configured, return a test response
        if not os.environ.get('OPENAI_API_KEY'):
            logger.warning("OpenAI API key not configured, returning test response")
            return jsonify({
                'answer': 'This is a test response. The OpenAI API key is not configured.',
                'error': 'OpenAI API key not configured'
            })
        
        # Create messages for the chat
        system_prompt = """You are a financial document assistant for BB.Borrower GmbH. 
Your task is to answer questions ONLY based on the information provided in the document context below.

IMPORTANT INSTRUCTIONS:
1. ONLY use information from the provided context
2. If the information is not in the context, say "I cannot find information about that in the documents"
3. ALWAYS cite your sources by mentioning the specific document name (e.g., "According to the Investment Memo...")
4. Be specific and provide details from the documents
5. When dates, figures, or specific data points are mentioned in the documents, include them in your answer

Remember, your answers must be accurate and factual based ONLY on what is stated in the documents."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
        
        # Get response from OpenAI
        try:
            logger.info("Sending request to OpenAI")
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message['content']
            logger.info(f"Answer received (first 100 chars): {answer[:100]}...")
            return jsonify({'answer': answer})
        except Exception as e:
            logger.error(f"Error getting response from OpenAI: {str(e)}")
            return jsonify({'error': f"Error getting response from OpenAI: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Unhandled error in /ask endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use Railway's PORT if provided, otherwise default to 5002
    port = int(os.environ.get('PORT', 5002))
    
    # Set debug to False in production
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting server on port {port} with debug={debug}")
    logger.info(f"Visit http://127.0.0.1:{port} to access the application")
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=debug) 