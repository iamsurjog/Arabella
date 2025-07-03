# Contains the core RAG functions so it is easier to work with it later
from ingest import read
# from script.add_file import add_to_kb
import ollama

class Core:
    def __init__(self, EMBEDDING_MODEL, LANGUAGE_MODEL):
        self.EMBEDDING_MODEL = EMBEDDING_MODEL
        self.LANGUAGE_MODEL = LANGUAGE_MODEL
        self.VECTOR_DB = list()
        self.history = False
        self.chat = []
        self.VECTOR_DICT = dict()

    def cosine_similarity(self, a, b):
        dot_product = sum([x * y for x, y in zip(a, b)])
        norm_a = sum([x ** 2 for x in a]) ** 0.5
        norm_b = sum([x ** 2 for x in b]) ** 0.5
        return dot_product / (norm_a * norm_b)


    def retrieve(self, query, top_n=3):
        query_embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=query)['embeddings'][0]
        # temporary list to store (chunk, similarity) pairs
        similarities = []
        for chunk, embedding in self.VECTOR_DB:
            similarity = self.cosine_similarity(query_embedding, embedding)
            similarities.append((chunk, similarity))
        # sort by similarity in descending order, because higher similarity means more relevant chunks
        similarities.sort(key=lambda x: x[1], reverse=True)
        # finally, return the top N most relevant chunks
        return similarities[:top_n]

    def generate(self, input_query):
        retrieved_knowledge = self.retrieve(input_query)
        instruction_prompt = '''You are a helpful chatbot.
        Use only the following pieces of context to answer the question. Don't make up any new information. However if you need to acquire some information from your own knowledge base, make sure to explicitly and clearly mention that it is the case: \n
        ''' + ('\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge]))
        # print('\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge]))
        # print(instruction_prompt)
        
        msgs = [
            {'role': 'system', 'content': instruction_prompt},
            {'role': 'user', 'content': input_query},
          ]
        if self.history:
            msgs.extend(self.chat)
        stream = ollama.chat(
          model=self.LANGUAGE_MODEL,
          messages=msgs,
          stream=True,
        )
        output = ""
        for chunk in stream:
            output += chunk['message']['content']
        if self.history:
            self.chat.append({'role': 'assistant', 'content': output})
        return output
    
    def clear_history(self):
        self.chat = []

    def add_files(self, fpath):
        dataset = read(fpath)
        # print(dataset)
        VECTOR_DB_Local = []
    
        for i, chunk in enumerate(dataset):
            VECTOR_DB_Local.append(self.add_chunk_to_database(chunk))
            print(f'Added chunk {i+1}/{len(dataset)} to the database')

        self.VECTOR_DICT[fpath] = VECTOR_DB_Local
        self.VECTOR_DB.extend(VECTOR_DB_Local)

    def remove_files(self, fpath):
        if fpath in self.VECTOR_DICT:
            for i in self.VECTOR_DICT[fpath]:
                self.VECTOR_DB.remove(i)

    def add_chunk_to_database(self, chunk):
        embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=chunk)['embeddings'][0]
        return (chunk, embedding)

