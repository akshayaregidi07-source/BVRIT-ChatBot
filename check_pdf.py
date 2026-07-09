"""Check what's in the vector store and PDF."""
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Check vector store
e = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENROUTER_API_KEY'),
    openai_api_base='https://openrouter.ai/api/v1',
    model='text-embedding-3-small'
)
v = Chroma(persist_directory='./chroma_db', embedding_function=e)
count = v._collection.count()
print(f'Vector store has {count} vectors')

# Search for fee-related content
docs = v.similarity_search('B.Tech fees tuition cost', k=5)
print(f'\nFound {len(docs)} docs for fee query:')
for i, d in enumerate(docs):
    print(f'  [{i+1}] Page {d.metadata.get("page", "?")}: {d.page_content[:200]}...')

# Also check what the PDF contains
print('\n\n--- Checking PDF content ---')
import fitz
pdf_path = './data/bvrit_college_info.pdf'
doc = fitz.open(pdf_path)
print(f'PDF has {doc.page_count} pages')
for page_num in range(doc.page_count):
    page = doc[page_num]
    text = page.get_text()
    print(f'\n--- Page {page_num + 1} ---')
    print(text[:500])
doc.close()