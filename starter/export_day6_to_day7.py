"""Export exact Day 6 payloads; never silently rechunk under existing vector IDs."""
import argparse
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from configs import ROOT, write_json, digest
from dotenv import load_dotenv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection',default='rag_strategy_b')
    parser.add_argument('--output',type=Path,default=ROOT/'data/chunks.json')
    args=parser.parse_args()
    load_dotenv(ROOT/'.env')
    from qdrant_client import QdrantClient
    client=QdrantClient(url=os.environ['QDRANT_URL'],api_key=os.getenv('QDRANT_API_KEY'),port=443,timeout=20)
    info=client.get_collection(args.collection)
    vector_config = info.config.params.vectors
    if isinstance(vector_config, dict):raise ValueError('Expected a single unnamed vector configuration.')
    if vector_config.distance.value != 'Cosine':raise ValueError('Expected the Day 6 Cosine index.')
    if vector_config.size != 384:
        raise ValueError('Expected Day 6 384-dimensional vector index.')
    chunks=[];offset=None
    while True:
        rows,offset=client.scroll(args.collection,limit=256,offset=offset,with_payload=True,with_vectors=False)
        for row in rows:
            p=row.payload
            chunks.append({'id':p['chunk_id'],'source_id':p['document_id'], 'source':p['source'],
                'page':p['page'],'text':p['text'],
                'metadata':{k:v for k,v in p.items() if k not in ('chunk_id','document_id','source','page','text')}})
        if offset is None:break
    chunks.sort(key=lambda c:(c['source_id'],c['page'],c['metadata'].get('chunk_index',0)))
    if len({c['id'] for c in chunks}) != len(chunks):raise ValueError('Duplicate chunk IDs.')
    if len(chunks) != info.points_count:raise ValueError('Point count changed during export; export again from a stable index.')
    pdf=ROOT/'data/cme2._suy_timgs_minh.pdf'
    logging.getLogger('pypdf').setLevel(logging.ERROR)
    from pypdf import PdfReader
    pages=len(PdfReader(pdf).pages) if pdf.exists() else None
    embedding=os.environ.get('EMBEDDING_MODEL')
    if not embedding:raise ValueError('Set EMBEDDING_MODEL to the verified Day 6 model; dimension alone cannot identify it.')
    write_json(args.output,chunks)
    write_json(args.output.parent/'corpus_manifest.json',{
        'pdf_pages':pages, 'pdf_sha256':digest(pdf) if pdf.exists() else None,'chunks':len(chunks),'index_points':info.points_count,'unique_chunk_ids':len({c['id'] for c in chunks}),
        'payload_text_match_count':len(chunks),'corpus_sha256':digest(args.output),
        'embedding':embedding,'embedding_provenance':'Student-supplied Day 6 configuration; Qdrant dimension alone does not verify model identity.',
        'dimensions':vector_config.size,'distance':vector_config.distance.value,
        'collection':args.collection,'verified_at':datetime.now(timezone.utc).isoformat(),
        'export':'Exact Qdrant Day 6 payloads; whitespace and original chunk boundaries retained.',
        'rights_status':'Student must confirm source/distribution permission; learning purpose alone is not a license.'})
    print(f'Exported {len(chunks)} original Day 6 chunks; no remote index changes.')

if __name__=='__main__':main()
