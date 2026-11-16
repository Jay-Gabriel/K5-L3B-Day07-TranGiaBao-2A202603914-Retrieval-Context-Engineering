"""Opt-in connection check. Does not list other collections or print keys."""
import os
from configs import ROOT
from dotenv import load_dotenv


def main():
    load_dotenv(ROOT/'.env')
    from qdrant_client import QdrantClient
    client=QdrantClient(url=os.environ['QDRANT_URL'],api_key=os.getenv('QDRANT_API_KEY'),port=443,timeout=15)
    name=os.getenv('QDRANT_COLLECTION','rag_strategy_b')
    info=client.get_collection(name)
    print('Collection:',name,'points:',info.points_count,'vectors:',info.config.params.vectors)

if __name__=='__main__':main()
