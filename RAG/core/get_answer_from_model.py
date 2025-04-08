import uuid
from core.convertor import Convertor
from core.spliter import split_text_into_chunks
from core.loaders.pdf_loader import PDFLoader 
from core.chromadbinit import collection
from core.llm_client.hiast_client import HiastClient
from typing import List
from core.llm_client.groq_client import GroqClient
from core.llm_client.llm_client_service import LLMClientService
import json
from core.file_tracker import FileTracker
def get_answer_from_model(client: LLMClientService, docpaths: List[str], chunks: int, numofresults: int, question: str, history: List[str]):
    print(f"Chunks: {chunks}, Num of results: {numofresults}, History: {history}, Question: {question}")

    fulldocs = []
    for file in docpaths:
        try:
            documents = PDFLoader(file)  # Load the PDF document
            documents = Convertor(documents)  # Convert the document
            docs = documents.convert()
            
            if not docs:
                print(f"Warning: No text found in {file}")
                continue
            
            print(f"Loaded document: {file}")
            
            # Split the document into chunks
            docs = split_text_into_chunks(docs, chunks, 40)
            
            if not docs:
                print(f"Warning: Document {file} could not be split into chunks.")
                continue
            
            fulldocs.extend(docs)
            print(f"Chunks for {file}: {docs}")
        
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    # Check if fulldocs is not empty
    if not fulldocs:
        raise ValueError("No valid documents were found. Cannot proceed with an empty document list.")
    
    # Generate unique IDs for each document chunk
    ids = [str(uuid.uuid4()) for _ in range(len(fulldocs))]
    
    if len(ids) != len(fulldocs):
        raise ValueError(f"Number of IDs {len(ids)} does not match the number of document chunks {len(fulldocs)}")
    
    print(f"Adding {len(fulldocs)} documents with {len(ids)} ids to the collection.")
    
    # Add the documents to the collection
    try:
        collection.add(
            documents=fulldocs,
            ids=ids
        )
    except Exception as e:
        raise RuntimeError(f"Error adding documents to collection: {e}")

    # preprocessing_using_chat = f"""
    # Given the following chat history,
    # edit the user question to provide any information from the chat history that would be needed to make the last user question make sense out of context:
    # History: {}
    # Last Question: {question}
    # Edited Question:    
    # """
    preprocessing_without_context= f"""
    You are an assistant for question-answering tasks from a specific file.
    Use the following question to retrive infromation from it and give me 5 questions maxiumum you need to retrive from the file not from the user to be able to answer correctly.
    dont answer the question yet just ask about more information you need to know give me questions only number each one of them in new line.
    the question is:
    Question: {question} 
    """
    preprocessing_without_context2= f"""
    You are an assistant for question-answering tasks from a specific file.
    Use the following question to retrive infromation from it and keywords which  in the question to be able to answer correctly.
    dont answer the question yet just give the keyword that might give you more information you need to know to answer correctly.
    give me the keywords only do not talk at all
    the question is:
    Question: {question} 
    """

    response = client.chat('user',preprocessing_without_context2)

    context=""
    keywordList = response['message'].split("\n")
    print(keywordList)
    for keywd in keywordList:
        results=collection.query(
        query_texts=[keywd],
        n_results=numofresults 
        )
        for doc in results["documents"][0]:
            context+=doc+"\n"
    results = collection.query(
        query_texts=[question],
        n_results=numofresults 
    )
    
    tmp =""
    for doc in results["documents"][0]:
        tmp+=doc+"\n"
    keywordContext=context
    QuestionContext = tmp
    QuestionAndKeyWordContext=context+"\n"+tmp
    print(history)
    template=f"""
    You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question.  
    answer in five sentences maximum keep the answer concise.
    also i will provide you with the history that would be needed
    history:{history}
    Question: {question} 
    Context: {QuestionContext} 
    Answer:
    """

    response = client.chat('user',template)
  
    collection.delete(ids=ids)
    return response
