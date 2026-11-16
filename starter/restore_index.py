"""Recreate the supplied corpus in a NEW Qdrant collection; never overwrite one."""
import argparse
import os
import uuid
from configs import load_data
from dotenv import load_dotenv
from pathlib import Path


def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection',required=True,help='New collection name on your own Qdrant instance')
    args=parser.parse_args()
    from qdrant_client import QdrantClient, models
    from fastembed import TextEmbedding
    client=QdrantClient(url=os.environ['QDRANT_URL'],api_key=os.getenv('QDRANT_API_KEY'),port=443,timeout=30)
    if client.collection_exists(args.collection):
        raise ValueError('Collection already exists; choose a new name. No data was overwritten.')
    chunks,_,_=load_data()
    embedder=TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
    vectors=list(embedder.embed([c['text'] for c in chunks]))
    client.create_collection(args.collection,vectors_config=models.VectorParams(size=384,distance=models.Distance.COSINE))
    client.upsert(args.collection,points=[models.PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL,c['id'])),vector=v.tolist(),payload={
            **c['metadata'],'chunk_id':c['id'],'document_id':c['source_id'],
            'source':c['source'],'page':c['page'],'text':c['text']}) for c,v in zip(chunks,vectors)],wait=True)
    print(f'Created {args.collection} with {len(chunks)} points. Set QDRANT_COLLECTION to use this collection.')

if __name__=='__main__':main()
