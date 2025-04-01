import os
from flask import Flask, render_template, request, jsonify
from docx import Document
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Debug logging
print("Environment variables:")
print("OPENAI_API_KEY exists:", bool(os.getenv('OPENAI_API_KEY')))
print("OPENAI_API_KEY length:", len(os.getenv('OPENAI_API_KEY', '')))
print("FLASK_ENV:", os.getenv('FLASK_ENV'))
print("PORT:", os.getenv('PORT'))
print("All environment variables:", dict(os.environ))

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client with error handling
try:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY is empty or not set")
        print("Current working directory:", os.getcwd())
        print("Files in current directory:", os.listdir())
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully")
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    print("Error type:", type(e).__name__)
    print("Full error details:", e)
    raise

# Global variable to store document contents
documents = []

def process_documents():
    """Process all documents in the Inputs files folder."""
    global documents
    input_dir = "Inputs files"
    
    print("Starting document processing...")
    print("Looking in directory:", input_dir)
    
    for filename in os.listdir(input_dir):
        print("Found file:", filename)
        if not filename.endswith('.docx'):  # Skip non-Word documents for now
            print("Skipping non-Word document:", filename)
            continue
            
        file_path = os.path.join(input_dir, filename)
        try:
            # Process Word documents
            doc = Document(file_path)
            print("Processing Word document:", filename)
            
            # Extract text with better structure preservation
            content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():  # Only include non-empty paragraphs
                    # Preserve any heading styles
                    if paragraph.style.name.startswith('Heading'):
                        content.append("## {}".format(paragraph.text))
                    else:
                        content.append(paragraph.text)
            
            # Join with double newlines to preserve paragraph structure
            text = '\n\n'.join(content)
            
            documents.append({
                'filename': filename,
                'content': text,
                'sections': [],  # We'll populate this in a moment
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            print("Successfully processed:", filename)
            print("Content length:", len(text), "characters")
            
            # Try to identify document sections
            current_section = {'title': 'Introduction', 'content': []}
            sections = []
            
            for line in content:
                if line.startswith('##'):  # It's a heading
                    if current_section['content']:
                        sections.append(current_section)
                    current_section = {
                        'title': line.replace('##', '').strip(),
                        'content': []
                    }
                else:
                    current_section['content'].append(line)
            
            if current_section['content']:
                sections.append(current_section)
            
            documents[-1]['sections'] = sections
            print("Number of sections found:", len(sections))
            
        except Exception as e:
            print("Error processing {}: {}".format(filename, str(e)))
    
    print("Document processing complete.")
    print("Total documents processed:", len(documents))
    for doc in documents:
        print("-", doc['filename'], "(", len(doc['content']), "characters )")

def find_relevant_context(query, full_context, max_chars=14000):
    """Find the most relevant parts of the context for the query."""
    if not documents:
        return ""
    
    try:
        # Keywords to identify relevant documents
        covenant_keywords = ['covenant', 'breach', 'compliance', 'violation', 'default']
        is_covenant_query = any(keyword in query.lower() for keyword in covenant_keywords)
        
        # Sort documents by relevance
        sorted_docs = []
        for doc in documents:
            relevance_score = 0
            filename = doc['filename'].lower()
            content = doc['content'].lower()
            
            # Only include documents that are relevant to the query
            if len(query.strip()) > 1:  # Only apply relevance scoring for queries longer than 1 character
                # Check if query terms appear in the document
                query_terms = query.lower().split()
                for term in query_terms:
                    if term in content:
                        relevance_score += 50
                
                # Prioritize compliance certificates for covenant queries
                if is_covenant_query and 'compliance' in filename:
                    relevance_score += 100
                
                # Prioritize more recent documents
                if '2025' in filename:
                    relevance_score += 50
                elif '2024' in filename:
                    relevance_score += 25
            else:
                # For very short queries, just include the most recent documents
                if '2025' in filename:
                    relevance_score += 100
                elif '2024' in filename:
                    relevance_score += 50
                
            sorted_docs.append((relevance_score, doc))
        
        # Sort by relevance score (highest first)
        sorted_docs.sort(reverse=True)
        
        # Build context from most relevant documents
        context_parts = []
        total_chars = 0
        
        for _, doc in sorted_docs:
            # Skip documents with zero relevance score for non-trivial queries
            if len(query.strip()) > 1 and relevance_score == 0:
                continue
                
            doc_content = "\n\n### Document: {}\n\n".format(doc['filename'])
            
            # Add section-based content if available
            if doc['sections']:
                for section in doc['sections']:
                    section_content = "## {}\n".format(section['title']) + '\n'.join(section['content'])
                    doc_content += section_content + "\n\n"
            else:
                doc_content += doc['content']
            
            if total_chars + len(doc_content) <= max_chars:
                context_parts.append(doc_content)
                total_chars += len(doc_content)
            else:
                # If we can't fit the whole document, add as much as we can
                remaining = max_chars - total_chars
                if remaining > 1000:  # Only add if we can include a meaningful chunk
                    context_parts.append(doc_content[:remaining])
                break
        
        return '\n\n'.join(context_parts)
    except Exception as e:
        print("Error in find_relevant_context:", str(e))
        # Fallback to simple context if there's an error
        return full_context[:max_chars]

def generate_answer(query):
    """Generate an answer using OpenAI's API"""
    try:
        # Prepare context from all documents
        full_context = ""
        for doc in documents:
            full_context += "\n\nDocument: {}\n{}\n".format(doc['filename'], doc['content'])

        # Find relevant context with increased max_chars
        relevant_context = find_relevant_context(query, full_context)
        
        print("Query:", query)
        print("Context length:", len(relevant_context))
        
        # Prepare the system prompt
        system_prompt = """You are a professional financial analyst and legal document expert. Your task is to analyze legal and financial documents and provide clear, accurate, and well-structured answers to questions about them.

Key guidelines for your responses:
1. Be comprehensive but concise
2. Structure your response with clear sections using markdown formatting
3. Use bullet points for lists
4. Highlight key information in bold
5. Include specific details from the documents
6. If information is not available in the documents, clearly state that
7. Maintain a professional tone
8. Be precise with numbers and dates
9. Use proper financial terminology
10. If discussing covenants or compliance, clearly state the status

Format your response using markdown:
- Use **bold** for important points
- Use bullet points for lists
- Use > for important quotes
- Use ### for section headers
- Keep paragraphs short and focused
- Use tables when presenting structured data

Remember to:
- Always base your answers on the provided documents
- Be clear about what information is and isn't available
- Structure complex information in an easy-to-read format
- Use professional financial and legal terminology appropriately"""

        # Prepare the user prompt
        user_prompt = f"""Based on the following documents, please answer this question: {query}

Relevant document sections:
{relevant_context}

Please provide a clear, well-structured answer using markdown formatting."""

        print("Sending request to OpenAI API...")
        # Call OpenAI API with increased temperature for more natural responses
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,  # Increased from 0.3 for more natural responses
            max_tokens=1000   # Reduced from 2000 to encourage conciseness
        )
        print("Received response from OpenAI API")

        return response.choices[0].message.content

    except Exception as e:
        print("Error generating answer:")
        print("Error type:", type(e).__name__)
        print("Error message:", str(e))
        print("Full error details:", e)
        return "I apologize, but I encountered an error while generating the answer. Please try again."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    answer = generate_answer(query)
    
    return jsonify({
        'answer': answer
    })

if __name__ == '__main__':
    # Process documents when starting the application
    process_documents()
    # Get port from environment variable (for Railway) or use default
    port = int(os.getenv('PORT', 8000))
    # Only enable debug mode if not in production
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug) 