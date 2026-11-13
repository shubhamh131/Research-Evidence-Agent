from app.collection.search import search_semantic_scholar

for p in search_semantic_scholar("LSTM vs transformer time series forecasting"):
    print(p.year, p.arxiv_id, p.title)
