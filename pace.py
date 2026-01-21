import os
import shutil
import sys
import argparse
from tqdm import tqdm

# --- CONFIGURAÇÕES DE CAMINHOS ---

# 1. Configuração da Origem (Rede)
MOUNT_POINT_REDE = "/Volumes/Downloads" # Apenas para verificação
DIR_ORIGEM_MUSICAS = "/Volumes/Downloads/pace/musicas"
DIR_ORIGEM_PODCASTS = "/Volumes/Downloads/pace/podcasts"

# 2. Configuração do Destino (iPod)
CAMINHO_IPOD_RAIZ = "/Volumes/IPOD"
BASE_IPOD_MUSIC = os.path.join(CAMINHO_IPOD_RAIZ, "iPod_Control", "Music")

# Define as subpastas específicas no destino
DIR_DESTINO_MUSICAS = os.path.join(BASE_IPOD_MUSIC, "Musicas")
DIR_DESTINO_PODCASTS = os.path.join(BASE_IPOD_MUSIC, "Podcasts")

def verificar_montagem():
    """Verifica se a unidade de rede e o iPod estão montados."""
    if not os.path.exists(MOUNT_POINT_REDE):
        print(f"❌ ERRO: Unidade de rede não encontrada: {MOUNT_POINT_REDE}")
        return False
    if not os.path.exists(CAMINHO_IPOD_RAIZ):
        print(f"❌ ERRO: iPod não encontrado: {CAMINHO_IPOD_RAIZ}")
        return False
    return True

def limpar_pasta_especifica(caminho):
    """
    Apaga e recria uma pasta específica.
    Usado para limpar 'Musicas' sem tocar em 'Podcasts' e vice-versa.
    """
    if os.path.exists(caminho):
        try:
            # print(f"🧹 Limpando: {caminho}") # Descomente para log detalhado
            shutil.rmtree(caminho)
            os.makedirs(caminho)
        except OSError as e:
            sys.exit(f"❌ Erro ao limpar pasta {caminho}: {e}")
    else:
        os.makedirs(caminho, exist_ok=True)

def mapear_arquivos(pares_origem_destino):
    """
    Recebe uma lista de tuplas [(Origem1, Destino1), (Origem2, Destino2)...]
    Retorna a lista de arquivos individuais para copiar e o tamanho total.
    """
    lista_copia = []
    total_bytes = 0
    
    print("📦 Mapeando arquivos...")

    for pasta_origem, pasta_destino in pares_origem_destino:
        if not os.path.exists(pasta_origem):
            print(f"⚠️  Aviso: Pasta de origem não encontrada: {pasta_origem}")
            continue

        # Caminha pela pasta de origem
        for root, _, files in os.walk(pasta_origem):
            for file in files:
                if file.startswith('.'): continue
                
                caminho_arquivo_origem = os.path.join(root, file)
                
                # Calcula o caminho relativo para manter a estrutura de subpastas
                # Ex: Origem/Rock/song.mp3 -> Destino/Rock/song.mp3
                caminho_relativo = os.path.relpath(caminho_arquivo_origem, pasta_origem)
                caminho_arquivo_destino = os.path.join(pasta_destino, caminho_relativo)
                
                try:
                    tamanho = os.path.getsize(caminho_arquivo_origem)
                    total_bytes += tamanho
                    lista_copia.append((caminho_arquivo_origem, caminho_arquivo_destino))
                except OSError:
                    pass
    
    return lista_copia, total_bytes

def obter_modo_operacao():
    """Define o modo via argumento CLI ou menu interativo."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", choices=['musicas', 'podcasts', 'ambos'], 
                        help="Modo de operação")
    args, _ = parser.parse_known_args()

    if args.modo:
        return args.modo

    print("\nO que você deseja sincronizar?")
    print(f"1 - Apenas Músicas (Mantém Podcasts intactos)")
    print(f"2 - Apenas Podcasts (Mantém Músicas intactas)")
    print(f"3 - Ambos (Apaga e recria tudo)")
    
    escolha = input("Escolha (1/2/3): ").strip()
    if escolha == '1': return 'musicas'
    if escolha == '2': return 'podcasts'
    return 'ambos'

def main():
    if not verificar_montagem():
        sys.exit(1)

    modo = obter_modo_operacao()
    
    # Lista de tarefas: [(PastaOrigem, PastaDestino), ...]
    tarefas = []

    if modo == 'musicas':
        print("🎵 Modo: Atualizando Músicas...")
        tarefas.append((DIR_ORIGEM_MUSICAS, DIR_DESTINO_MUSICAS))
        
    elif modo == 'podcasts':
        print("🎙️ Modo: Atualizando Podcasts...")
        tarefas.append((DIR_ORIGEM_PODCASTS, DIR_DESTINO_PODCASTS))
        
    else: # ambos
        print("🚀 Modo: Atualizando Tudo...")
        tarefas.append((DIR_ORIGEM_MUSICAS, DIR_DESTINO_MUSICAS))
        tarefas.append((DIR_ORIGEM_PODCASTS, DIR_DESTINO_PODCASTS))

    # 1. Limpeza Seletiva
    # O script percorre as tarefas e limpa APENAS os destinos envolvidos.
    print("🧹 Preparando pastas de destino...")
    for _, destino in tarefas:
        limpar_pasta_especifica(destino)

    # 2. Mapeamento
    arquivos, tamanho_total = mapear_arquivos(tarefas)

    if not arquivos:
        print("⚠️  Nenhum arquivo encontrado para copiar.")
        return

    # 3. Execução da Cópia
    with tqdm(total=tamanho_total, unit='B', unit_scale=True, desc="Copiando") as barra:
        for origem, destino in arquivos:
            print(f"{origem} ----> {destino}")
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                shutil.copy2(origem, destino)
                barra.update(os.path.getsize(origem))
            except Exception as e:
                print(f"❌ Erro ao copiar {os.path.basename(origem)}: {e}")
    ipod_cmd = "python3 ipod-shuffle-4g.py --verbose --auto-id3-playlists --track-voiceover --playlist-voiceover --rename-unicode /Volumes/IPOD"
    os.system(ipod_cmd)
    print("\n✨ Sincronização finalizada com sucesso!")

if __name__ == "__main__":
    main()