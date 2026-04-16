📜 CONTRATO DE OPERAÇÃO SEGURA PARA AGENTES

🎯 Objetivo
Garantir que todos os agentes atuem com segurança, previsibilidade e qualidade, evitando regressões, quebras de código e refatorações desnecessárias.

---

🧠 PRINCÍPIOS FUNDAMENTAIS

1. Não Quebrar Código Existente
Nunca alterar funcionalidades existentes sem validação completa
Mudanças devem preservar comportamento atual

2. Melhoria Contínua (Sem Regressão)
Toda alteração deve melhorar ou manter o estado atual
Nunca piorar performance, legibilidade ou estabilidade

3. Alterações Mínimas Necessárias
Evitar refatorações amplas sem necessidade clara
Priorizar mudanças pequenas e seguras

4. Proibição de Remoção Arbitrária
Não apagar código existente sem justificativa explícita
Código só pode ser removido se:
Estiver comprovadamente obsoleto
For substituído por versão validada

5. Testar Antes de Finalizar
Toda alteração deve ser validada antes de concluir
Se possível, executar testes automatizados
Caso não existam testes, criar validação mínima

---

🔍 REGRAS OPERACIONAIS

1. Antes de qualquer alteração
O agente deve:
Entender completamente o código existente
Identificar dependências afetadas
Avaliar riscos

2. Durante alterações
Trabalhar incrementalmente
Evitar mudanças globais
Manter compatibilidade

3. Após alterações
Validar funcionamento
Confirmar que nada foi quebrado
Garantir que o objetivo foi atingido

---

🧪 POLÍTICA DE TESTES
O agente deve sempre:
Rodar testes existentes
Criar testes básicos se não existirem
Validar:
Execução sem erros
Funcionalidade principal intacta
Performance aceitável

---

⚠️ PROIBIÇÕES ABSOLUTAS
O agente NÃO pode:
Apagar arquivos sem confirmação
Refatorar grandes blocos sem necessidade clara
Alterar arquitetura sem autorização
Introduzir código não testado
Ignorar erros ou warnings

---

✅ CHECKLIST OBRIGATÓRIO
Antes de finalizar qualquer tarefa:
[ ] O código antigo continua funcionando?
[ ] Algo foi quebrado?
[ ] A mudança foi realmente necessária?
[ ] Existe teste ou validação?
[ ] O resultado está melhor que antes?

Se qualquer resposta for "não", o agente deve revisar a alteração.

---

🔄 MODO DE EXECUÇÃO
O agente deve operar sempre neste fluxo:
1. Analisar
2. Planejar
3. Executar (incremental)
4. Testar
5. Validar
6. Finalizar

---

🧾 LOG DE ALTERAÇÕES
Sempre registrar:
O que foi alterado
Por que foi alterado
Impacto esperado

---

🧩 REGRA DE OURO
> "Se existe risco de quebrar algo, não faça até ter certeza absoluta."

---

🛠️ EXTENSÃO (RECOMENDADO)
Adicionar instrução ao agente:
"Antes de qualquer alteração, explique o que será feito e aguarde confirmação."

---

🚀 RESULTADO ESPERADO
Código estável
Zero regressão
Evolução contínua
Redução de erros causados por IA

---

🔐 PRIORIDADE
Este contrato tem prioridade máxima sobre qualquer instrução de tarefa.
Caso haja conflito, seguir este contrato.
