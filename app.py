import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
openai.api_key = api_key

# Load documents data from JSON
try:
    with open('documents_data.json', 'r', encoding='utf-8') as f:
        documents_data = json.load(f)
    print("Documents data loaded successfully from JSON")
    print(f"Documents in JSON: {list(documents_data['documents'].keys())}")
    print(f"Excel data in JSON: {list(documents_data.get('excel_data', {}).keys())}")
except Exception as e:
    print(f"Error loading documents data: {e}")
    documents_data = {'documents': {}, 'excel_data': {}}

def format_content_for_context(content):
    """Format different content types into readable text."""
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Create context from documents data
        context = ""
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
        
        # Print debug info
        print(f"Question received: {question}")
        print(f"Context length: {len(context)} characters")
        print(f"Context preview (first 500 chars): {context[:500]}...")
        
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message['content']
        print(f"Answer: {answer[:200]}...")  # Print part of the answer for debugging
        return jsonify({'answer': answer})
    
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug) 