"""Opt-in live smoke test, separate from held-out benchmark."""
import argparse
import json
from agentic import run_agent
from controller import GeminiController
from configs import CONFIGS,load_data,build_retrievers


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',choices=CONFIGS,default='lexical_context')
    parser.add_argument('--question',default='Hai biểu hiện lâm sàng chính của suy tim được bài giảng nêu là gì?')
    args=parser.parse_args();config=CONFIGS[args.config];chunks,_,_=load_data()
    retriever=build_retrievers(chunks,[config['method']])[config['method']]
    result=run_agent(args.question,GeminiController(max_searches=config['max_searches']),retriever,
                     max_searches=config['max_searches'],top_k=config['top_k'],budget=config['budget'])
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
