import chromadb

class RetrieverAgent:
    def __init__(self, db_path="./chroma_db", collection_name="bank_schema"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(collection_name)

    def fetch_schema_context(self, tables: list[str]) -> dict:
        context = []
        for table in tables:
            results = self.collection.query(
                query_texts=[table],
                n_results=1
            )
            if results and results["documents"]:
                context.append(results["documents"][0][0])
        return {"schema_context": context}
