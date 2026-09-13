"""
Worker: consome a fila e executa a inferencia.

O QUE JA ESTA PRONTO: o laco principal e o carregamento do modelo.
O QUE VOCE PRECISA FAZER (TAREFAS.md, itens 3 e 5):
  - guardar o resultado ao terminar
  - tratar erro com retentativa e fila de descarte (dead-letter)

Rodar:  python -m app.worker
Suba mais de um worker em terminais diferentes e veja a carga se dividir.
"""
import json
import time

from app import fila
from app.modelo import carregar_modelo

FILA_DESCARTE = "dead_letter"
MAX_TENTATIVAS = 3


def main():
    print("[worker] carregando modelo...")
    modelo = carregar_modelo()
    print("[worker] pronto. aguardando tarefas (Ctrl+C para sair)")

    while True:
        tarefa = fila.proxima_tarefa(timeout=5)
        if tarefa is None:
            continue

        print(f"[worker] processando {tarefa['id']}")
        inicio = time.time()
        try:
            if tarefa["texto"] == "__falhar__":
                raise RuntimeError("falha simulada para a tarefa 5")

            resultado = modelo.prever(tarefa["texto"])
            resultado["status"] = "pronto"
            resultado["tempo_ms"] = round((time.time() - inicio) * 1000, 2)

# ------------------------------------------------------------------
# TAREFA 3 - Guardar o resultado
# ------------------------------------------------------------------
            fila.guardar_resultado(tarefa["id"], resultado)

# ------------------------------------------------------------------
# TAREFA 5 - Retentativa + dead-letter em vez de so registrar.
# ------------------------------------------------------------------
        except Exception as erro:
            tentativas = tarefa.get("tentativas", 0) + 1
            tarefa["tentativas"] = tentativas
            print(f"[worker] ERRO em {tarefa['id']} (tentativa {tentativas}): {erro}")

            if tentativas < MAX_TENTATIVAS:
                fila.cliente().rpush(fila.FILA_TAREFAS, json.dumps(tarefa))
                print(f"[worker] reenfileirando {tarefa['id']}")
            else:
                fila.cliente().rpush(FILA_DESCARTE, json.dumps(tarefa))
                fila.guardar_resultado(
                    tarefa["id"],
                    {"status": "erro", "detalhe": str(erro)},
                )
                print(f"[worker] {tarefa['id']} enviado para dead-letter")


if __name__ == "__main__":
    main()
