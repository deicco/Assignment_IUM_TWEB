from pymongo import MongoClient


# 🔌 Connessione a MongoDB (puoi cambiarla se hai utente/password)
def get_mongo_client(uri="mongodb://localhost:27017/"):
    try:
        client = MongoClient(uri)
        # Test della connessione
        client.admin.command("ping")
        print("✅ Connessione a MongoDB riuscita")
        return client
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return None


# 💾 Salva un DataFrame pulito su MongoDB
def save_clean_reviews_to_mongo(df, db="mydatabase", collection="rotten_reviews", drop_existing=True):
    client = get_mongo_client()
    if not client:
        return

    db_ref = client[db]
    collection_ref = db_ref[collection]

    try:
        if drop_existing:
            collection_ref.drop()

        records = df.to_dict(orient="records")

        if records:
            collection_ref.insert_many(records)
            print(f"✅ {len(records)} documenti inseriti in {db}.{collection}")
        else:
            print("⚠️ Nessun dato da inserire.")
    except Exception as e:
        print(f"❌ Errore durante l'importazione: {e}")


# 🔍 Leggi i primi N documenti
def preview_collection(db="mydatabase", collection="rotten_reviews", limit=5):
    client = get_mongo_client()
    if not client:
        return

    try:
        docs = list(client[db][collection].find().limit(limit))
        print(f"📄 Preview dei primi {limit} documenti in {db}.{collection}:")
        for doc in docs:
            print(doc)
    except Exception as e:
        print(f"❌ Errore durante la lettura: {e}")


# 🔢 Conta i documenti in una collection
def count_documents(db="mydatabase", collection="rotten_reviews"):
    client = get_mongo_client()
    if not client:
        return

    try:
        count = client[db][collection].count_documents({})
        print(f"📊 Numero totale di documenti in {db}.{collection}: {count}")
        return count
    except Exception as e:
        print(f"❌ Errore durante il conteggio: {e}")
        return 0
