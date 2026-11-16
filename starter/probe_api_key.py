"""Check the configured model without printing credentials."""
from controller import GeminiController


def main():
    controller=GeminiController()
    result=controller.decide('Hai biểu hiện lâm sàng chính của suy tim là gì?',[])
    print('Model:',controller.model)
    print('Tool:',result['action'])
    print('Usage:',controller.calls[-1]['usage'])

if __name__=='__main__':main()
