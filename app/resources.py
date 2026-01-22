from schemas import CategoryEnum




# Base de conhecimento para a heurística
KEYWORDS = {
    CategoryEnum.FINANCEIRO: [
        "boleto", "pagar", "pagamento", "valor", "honorários", 
        "custas", "fatura", "dinheiro", "reembolso", "nota fiscal",
        "cobrança", "débito", "crédito", "transferência", "depósito",
        "juros", "multa", "taxa", "investimento", "orçamento",
        "custo", "despesa", "receita", "lucro", "prejuízo"
    ],
    CategoryEnum.PROCESSUAL: [
        "prazo", "juiz", "audiência", "processo", "liminar", 
        "sentença", "recurso", "intimação", "vara", "autos", "dje",
        "apelação", "agravado", "agravante", "juizado", "tribunal",
        "petição", "defesa", "réu", "autor", "sentenciado",
        "moção", "mandado", "citação", "contestação", "execução"
    ],
    CategoryEnum.SUPORTE: [
        "senha", "login", "acesso", "sistema", "erro", "bug", 
        "entrar", "site", "nexus", "indisponível", "offline",
        "problema técnico", "não funciona", "travado", "lento",
        "recuperar senha", "resetar", "autenticação", "permissão",
        "crash", "falha", "conexão", "servidor down", "manutenção"
    ],
    CategoryEnum.COMERCIAL: [
        "proposta", "orçamento", "contratar", "nova causa", 
        "parceria", "apresentação", "reunião comercial", "cliente novo",
        "negócio", "venda", "contrato", "acordo", "oportunidade",
        "consultoria", "projeto", "licitação", "fornecedor", "cliente",
        "prospecção", "oferta", "desconto", "cancelamento", "contratação"
    ],
    CategoryEnum.ADMINISTRATIVO: [
        "agendar", "sala", "reunião", "cópia", "digitalizar", 
        "documento", "certidão", "cartório", "motoboy", "correio",
        "agendamento", "recurso", "material", "logística", "secretária",
        "arquivos", "impressão", "scaneamento", "protocolo", "pasta",
        "solicitação", "administrativo", "gerencial", "coordenação", "organização"
    ]
}



# Template do Prompt do Sistema (LLM) com Few-Shot
SYSTEM_PROMPT_TEMPLATE = """
Você é um classificador jurídico especializado do sistema Nexus. Sua tarefa é analisar a mensagem do usuário e classificá-la em uma das seguintes categorias, baseando-se no **contexto e intenção**, não apenas em palavras isoladas.

CATEGORIAS:
1. **Processual**: Assuntos relacionados a processos judiciais, prazos, audiências, decisões, recursos, liminares, andamento processual.
2. **Financeiro**: Assuntos de pagamento, custas processuais, honorários, cobranças, faturas, reembolsos, fluxo de caixa.
3. **Suporte Técnico**: Problemas técnicos, acesso ao sistema, erros, bugs, autenticação, performance, indisponibilidade.
4. **Comercial**: Novos negócios, propostas comerciais, parcerias, prospecção de clientes, contratos, licitações.
5. **Administrativo**: Agendamentos, solicitação de documentos, logística, organização de recursos, secretaria.
6. **Outros**: Mensagens genéricas, saudações ou que não se encaixam nas categorias acima.

EXEMPLOS (Few-Shot):
- Entrada: "Qual o prazo para recurso de apelação neste processo?"
  Saída: {{"category": "Processual", "reasoning": "Questão sobre prazo e recurso processual"}}

- Entrada: "Preciso de uma cópia do processo, pode encaminhar por email?"
  Saída: {{"category": "Administrativo", "reasoning": "Solicitação de documento e logística de entrega"}}

- Entrada: "A tela está congelada, não consigo fazer login no sistema"
  Saída: {{"category": "Suporte Técnico", "reasoning": "Problema técnico de acesso ao sistema"}}

- Entrada: "Gostaria de receber uma proposta para novos casos de direito trabalhista"
  Saída: {{"category": "Comercial", "reasoning": "Interesse em novo negócio/contrato"}}

- Entrada: "Qual é o valor das custas processuais deste caso?"
  Saída: {{"category": "Financeiro", "reasoning": "Questão sobre valores e custas processuais"}}

INSTRUÇÕES:
- Analise o CONTEXTO e a INTENÇÃO da mensagem, não apenas palavras-chave isoladas
- Uma mensagem pode conter múltiplas palavras-chave, mas classifique pela intenção principal do usuário
- Seja consistente e lógico na classificação
- Retorne SEMPRE um JSON válido com as chaves 'category' (nome exato da categoria) e 'reasoning' (breve explicação)

CATEGORIAS DISPONÍVEIS: {categories}

Agora, classifique a mensagem do usuário:
"""