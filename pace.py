import os
import shutil
import sys
from tqdm import tqdm

# --- CONFIGURAÇÕES ---

# Caminho de origem (Unidade de Rede)
CAMINHO_ORIGEM = "/Volumes/Downloads/pace"

# Caminho da Raiz do iPod (Para verificação de montagem)
CAMINHO_IPOD_RAIZ = "/Volumes/IPOD"

# Caminho exato de destino solicitado
CAMINHO_DESTINO = os.path.join(CAMINHO_IPOD_RAIZ, "iPod_Control", "Music")

def verificar_montagem():
    """Verifica se as unidades estão acessíveis."""
    print("🔍 Verificando conexões...")
    
    if not os.path.exists(CAMINHO_ORIGEM):
        print(f"❌ ERRO: Origem não encontrada (verifique a rede):\n   -> {CAMINHO_ORIGEM}")
        return False
        
    if not os.path.exists(CAMINHO_IPOD_RAIZ):
        print(f"❌ ERRO: iPod não encontrado (verifique se está montado):\n   -> {CAMINHO_IPOD_RAIZ}")
        return False
        
    print("✅ Unidade de rede e iPod detectados.")
    return True

def limpar_destino():
    """
    Apaga TUDO dentro da pasta Music do iPod.
    """
    # Verifica se a pasta destino existe antes de tentar apagar
    if os.path.exists(CAMINHO_DESTINO):
        print("\n" + "!"*60)
        print(f"⚠️  PERIGO: Você está prestes a apagar TODAS as músicas em:")
        print(f"   -> {CAMINHO_DESTINO}")
        print("!"*60 + "\n")
        
        # --- TRAVA DE SEGURANÇA ---
        # Para remover a confirmação manual e tornar automático, 
        # apague ou comente as 4 linhas abaixo:
        confirmacao = input("Digite 'sim' para apagar o conteúdo do iPod e continuar: ").strip().lower()
        if confirmacao != 'sim':
            print("🚫 Operação cancelada.")
            sys.exit(0)
        # --------------------------

        print("🗑️  Limpando músicas antigas do iPod...")
        try:
            # Remove a pasta Music inteira
            shutil.rmtree(CAMINHO_DESTINO)
            # Recria a pasta Music vazia
            os.makedirs(CAMINHO_DESTINO)
            print("✅ Pasta Music limpa e recriada.")
        except OSError as e:
            print(f"❌ Erro ao limpar o iPod: {e}")
            sys.exit(1)
    else:
        # Se a pasta Music não existir (iPod formatado/novo), cria ela.
        print("📂 A pasta Music não existia, criando agora...")
        os.makedirs(CAMINHO_DESTINO, exist_ok=True)

def copiar_arquivos():
    # 1. Verifica montagem
    if not verificar_montagem():
        sys.exit(1)

    # 2. Limpa o destino (Cuidado: apaga arquivos)
    limpar_destino()

    # 3. Calcula arquivos para a barra de progresso
    print("📦 Mapeando arquivos da rede...")
    arquivos_para_copiar = []
    tamanho_total_bytes = 0

    for root, dirs, files in os.walk(CAMINHO_ORIGEM):
        for file in files:
            if file.startswith('.'): # Ignora .DS_Store e outros ocultos
                continue
            
            caminho_origem = os.path.join(root, file)
            
            # Preserva a estrutura de pastas dentro de Music?
            # Se quiser jogar tudo solto na raiz de Music, a lógica muda.
            # Aqui mantemos a estrutura original da pasta 'pace':
            caminho_relativo = os.path.relpath(caminho_origem, CAMINHO_ORIGEM)
            caminho_final = os.path.join(CAMINHO_DESTINO, caminho_relativo)
            
            try:
                tamanho = os.path.getsize(caminho_origem)
                tamanho_total_bytes += tamanho
                arquivos_para_copiar.append((caminho_origem, caminho_final))
            except OSError:
                pass

    if not arquivos_para_copiar:
        print("⚠️  Nenhum arquivo encontrado na origem.")
        return

    # 4. Executa a cópia
    print(f"🚀 Copiando {len(arquivos_para_copiar)} arquivos para o iPod...")
    
    # Configuração da barra de progresso
    with tqdm(total=tamanho_total_bytes, unit='B', unit_scale=True, unit_divisor=1024, desc="Sincronizando") as barra:
        for origem, destino in arquivos_para_copiar:
            try:
                # Cria subpastas se necessário
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                
                # Copia o arquivo
                shutil.copy2(origem, destino)
                
                # Atualiza barra
                barra.update(os.path.getsize(origem))
            except Exception as e:
                print(f"\n❌ Falha ao copiar {origem}: {e}")

if __name__ == "__main__":
    copiar_arquivos()
    ipod_cmd = "python3 ipod-shuffle-4g.py --verbose --auto-dir-playlists --track-voiceover --playlist-voiceover --rename-unicode /Volumes/IPOD"
    os.system(ipod_cmd)
    print("\n🎧 Sincronização com iPod finalizada!")