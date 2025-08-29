import chromadb

class RetrieverAgent:
    def __init__(self, db_path="./chroma_db", collection_name="bank_schema"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(collection_name)

    def fetch_schema_context(self, tables: list[str]) -> dict:
        context = []
        for table in tables:
            try:
                results = self.collection.query(
                    query_texts=[table],
                    n_results=1
                )
                if results and results["documents"] and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
                    context.append(results["documents"][0][0])
                else:
                    # Fallback: add basic table info if no schema found
                    context.append(f"Table: {table}")
            except Exception as e:
                print(f"Error retrieving schema for table {table}: {e}")
                # Fallback: add basic table info
                context.append(f"Table: {table}")
        return {"schema_context": context}
