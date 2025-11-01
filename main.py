from colorama import init, Fore, Style
init(autoreset=True)
import asyncio
import time
from src.transformer.transformer import Transformer
from src.api.anilist import AniListClient
from src.api.anizip import AniZipClient
from src.utils.remove_html_tags import remove_html_tags

def print_header(title, width=70):
    print(f"\n{Fore.CYAN}╔{'═' * (width-2)}{Fore.CYAN}╗{Style.RESET_ALL}")
    padding = (width - len(title) - 4) // 2
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.WHITE}{title}{' ' * (width - len(title) - padding - 4)} {Fore.CYAN}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚{'═' * (width-2)}{Fore.CYAN}╝{Style.RESET_ALL}")

def print_header2(title, width=70):
    print(f"\n{Fore.CYAN}╔{'═' * (width-2)}{Fore.CYAN}╗{Style.RESET_ALL}")
    padding = (width - len(title) - 4) // 2
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.WHITE}{title}{' ' * (width - len(title) - padding - 4)} {Fore.CYAN} ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚{'═' * (width-2)}{Fore.CYAN}╝{Style.RESET_ALL}")

def print_box(content, color=Fore.WHITE, width=70):
    lines = content.split('\n')
    print(f"{Fore.CYAN}┌{'─' * (width-2)}┐{Style.RESET_ALL}")
    for line in lines:
        padding = width - len(line) - 4
        print(f"{Fore.CYAN}│ {color}{line}{' ' * padding}{Fore.CYAN} │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└{'─' * (width-2)}┘{Style.RESET_ALL}")

def print_loading(message="Carregando"):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    print(f"\r{Fore.YELLOW}{frames[0]} {message}...{Style.RESET_ALL}", end='', flush=True)

def print_separator(char="─", width=70):
    print(f"{Fore.CYAN}{char * width}{Style.RESET_ALL}")

def print_menu_option(key, description, color=Fore.YELLOW):
    print(f"  {color}[{key}]{Style.RESET_ALL} {description}")

async def main():
    print_welcome()
    try:
        print_header("🔍 BUSCAR ANIME")
        anime_title = input(f"\n{Fore.LIGHTYELLOW_EX}  📝 Digite o nome do anime: {Style.RESET_ALL}")
        if anime_title.strip():
            await search_anime_api(anime_title)
        else:
            print(f"{Fore.RED}  ❌ Nome inválido!{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}  ⚠️  Operação cancelada pelo usuário{Style.RESET_ALL}")
    finally:
        bye = r''' /\_/\  
( o.o )  < bye bye!
 > ^ <
'''
        print(f"{Fore.GREEN}{bye}{Style.RESET_ALL}")

async def search_anime_api(title: str, limit: int = 10):
    """search animes in anilist by title, with interactive pagination."""
    import textwrap
    client = AniListClient()
    page = 1
    
    while True:
        print_loading(f"Buscando '{title}' (página {page})")
        results, total_pages = await client.search(title, limit=limit, page=page)
        print("\r" + " " * 80 + "\r", end='')  # Limpa linha de loading
        
        for anime in results:
            anime['description'] = remove_html_tags(anime['description'] or '')
        
        if not results:
            msg = "Nenhum anime encontrado" if page == 1 else "Nenhum resultado nesta página"
            print(f"\n{Fore.RED}  ❌ {msg}{Style.RESET_ALL}\n")
            return
        
        print_header2(f"RESULTADOS: {title}")
        print(f"\n{Fore.MAGENTA}  📊 Página {page}/{total_pages} • {len(results)} resultados{Fore.MAGENTA}{Style.RESET_ALL}\n")
        print_separator()
        for idx, anime in enumerate(results):
            title_display = anime['title_romaji'] or anime['title_english'] or anime['title_native']
            episodes = anime['episodes'] or '?'
            score = anime['average_score'] or 'N/A'
            
            print(f"\n{Fore.YELLOW}  [{idx}]{Style.RESET_ALL} {Fore.GREEN}{title_display}{Style.RESET_ALL}")
            print(f"      {Fore.BLUE}📺 {episodes} eps{Style.RESET_ALL} │ {Fore.YELLOW}⭐ {score}{Style.RESET_ALL}")
            desc = anime['description']
            if desc:
                desc_preview = textwrap.shorten(desc.replace('\n', ' '), width=90, placeholder='...')
                print(f"      {Fore.LIGHTBLACK_EX}{desc_preview}{Style.RESET_ALL}")
        
        # menu de navegação
        print_separator()
        print(f"\n{Fore.CYAN}  NAVEGAÇÃO:{Style.RESET_ALL}")
        print_menu_option("0-" + str(len(results)-1), "Ver detalhes do anime")
        if page < total_pages:
            print_menu_option("n", "Próxima página →")
        if page > 1:
            print_menu_option("p", "← Página anterior")
        print_menu_option("ENTER", "Sair")
        
        escolha = input(f"\n{Fore.LIGHTYELLOW_EX}  ➤ Sua escolha: {Style.RESET_ALL}").strip()
        
        if escolha == '':
            print(f"{Fore.YELLOW}  ← Saindo...{Style.RESET_ALL}")
            break
        
        if escolha.lower() == 'n':
            if page < total_pages:
                page += 1
            else:
                print(f"{Fore.YELLOW}  ⚠️  Já está na última página{Style.RESET_ALL}")
                time.sleep(1)
            continue
        
        if escolha.lower() == 'p':
            if page > 1:
                page -= 1
            else:
                print(f"{Fore.YELLOW}  ⚠️  Já está na primeira página{Style.RESET_ALL}")
                time.sleep(1)
            continue
        
        if escolha.isdigit() and 0 <= int(escolha) < len(results):
            idx = int(escolha)
            anime = results[idx]
            await show_anime_details(anime)
            break
        else:
            print(f"{Fore.RED}  ❌ Opção inválida!{Style.RESET_ALL}")
            time.sleep(1)
    
    await client.close()

async def show_anime_details(anime):
    """Exibe detalhes completos de um anime"""
    import textwrap
    
    print_header("📺 DETALHES DO ANIME")
    print(f"\n{Fore.CYAN}  TÍTULOS:{Style.RESET_ALL}")
    if anime['title_romaji']:
        print(f"    🌐 {anime['title_romaji']}")
    if anime['title_english']:
        print(f"    🇬🇧 {anime['title_english']}")
    if anime['title_native']:
        print(f"    🇯🇵 {anime['title_native']}")
    
    print(f"\n{Fore.CYAN}  INFORMAÇÕES:{Style.RESET_ALL}")
    print(f"    🆔 ID: {anime['id']}")
    print(f"    📺 Episódios: {anime['episodes'] or 'Desconhecido'}")
    print(f"    ⭐ Nota: {anime['average_score'] or 'N/A'}/100")
    if anime['description']:
        print(f"\n{Fore.CYAN}  SINOPSE:{Style.RESET_ALL}")
        wrapped = textwrap.fill(anime['description'], width=66)
        print_box(wrapped, Fore.LIGHTBLACK_EX)
    
    # menu dos detalhes
    while True:
        print_separator()
        print(f"\n{Fore.CYAN}  O QUE DESEJA FAZER?{Style.RESET_ALL}")
        print_menu_option("s", "🔍 Ver animes similares")
        print_menu_option("e", "📺 Ver lista de episódios")
        print_menu_option("ENTER", "← Sair")
        
        acao = input(f"\n{Fore.LIGHTYELLOW_EX}  ➤ Sua escolha: {Style.RESET_ALL}").strip().lower()
        
        if acao == 's':
            selected_title = anime.get('title_romaji') or anime.get('title_english') or anime.get('title_native')
            await show_similar_animes(selected_title, anime['id'])
            break
        elif acao == 'e':
            await show_anime_episodes(anime['id'])
            break
        elif acao == '':
            break
        else:
            print(f"{Fore.RED}  ❌ Opção inválida!{Style.RESET_ALL}")
            time.sleep(1)

async def show_anime_episodes(anilist_id: int):
    """search and show regular episodes of the anime by anilist_id using AniZipClient and extract_all_episodes_info."""
    client = AniZipClient()
    try:
        print_loading("Buscando episódios")
        response = await client.get_mappings(anilist_id)
        print("\r" + " " * 80 + "\r", end='')
        
        episodes_data = response.get('episodes', {})
        if not episodes_data:
            print(f"\n{Fore.RED}  ❌ Nenhum episódio encontrado{Style.RESET_ALL}\n")
            return
        
        episodes = client.extract_all_episodes_info(episodes_data, anilist_id)
        if not episodes:
            print(f"\n{Fore.RED}  ❌ Nenhum episódio regular encontrado{Style.RESET_ALL}\n")
            return
        
        print_header("📺 LISTA DE EPISÓDIOS")
        print(f"{Fore.MAGENTA}  Total: {len(episodes)} episódios{Style.RESET_ALL}")
        print_separator()
        
        episode_numbers = set()
        for ep in episodes:
            try:
                if ep['episode_number'] is not None:
                    episode_numbers.add(int(ep['episode_number']))
            except Exception:
                pass
        
        for ep in episodes:
            ep_num = str(ep['episode_number']) if ep['episode_number'] is not None else "?"
            ep_title = str(ep['episode_title']) if ep['episode_title'] is not None else "Sem título"
            
            print(f"\n{Fore.YELLOW}  EP {ep_num:>3}{Style.RESET_ALL} │ {Fore.WHITE}{ep_title}{Style.RESET_ALL}")
            
            summary = ep.get('synopsis') or ''
            if summary:
                summary_short = summary[:80] + ('...' if len(summary) > 80 else '')
                print(f"         {Fore.LIGHTBLACK_EX}{summary_short}{Style.RESET_ALL}")
        
        if episode_numbers:
            min_ep = min(episode_numbers)
            max_ep = max(episode_numbers)
            missing = [n for n in range(min_ep, max_ep + 1) if n not in episode_numbers]
            
            if missing:
                print(f"\n{Fore.RED}  ⚠️  EPISÓDIOS FALTANTES: {', '.join(map(str, missing))}{Style.RESET_ALL}")
        
        print()
    finally:
        await client.close()

async def show_similar_animes(selected_title: str, selected_id: int):
    """show the most similar animes to the selected title using the Transformer."""
    from src.transformer.transformer import Transformer
    from src.constants.cleaner import get_all_synopses
    from src.utils.path import get_dataset_csv_path
    
    transformer = Transformer()

    # configuração
    print_header2("⚙️ CONFIGURAÇÃO")
    print(f"\n{Fore.CYAN}  Quantos animes comparar do dataset?{Style.RESET_ALL}")
    print_menu_option("ENTER", "Padrão (500 animes)")
    print_menu_option("all", "TODO o dataset (pode demorar!)")
    print_menu_option("N", "Número específico")
    
    # pergunta ao usuário o limite de animes do dataset
    user_limit = input(f"\n{Fore.LIGHTYELLOW_EX}  ➤ Sua escolha: {Style.RESET_ALL}").strip().lower()
    
    if user_limit == "all":
        MAX_DATASET = 9999999  # valor alto para garantir que pega tudo
        print(f"\n{Fore.RED}  ⚠️  AVISO: Comparando com TODO o dataset. Isso pode demorar bastante, dependendo do tamanho do arquivo!{Style.RESET_ALL}")
        time.sleep(2)
    else:
        try:
            MAX_DATASET = int(user_limit) if user_limit else 500
        except Exception:
            MAX_DATASET = 500
    
    print_loading(f"Analisando {MAX_DATASET} animes")
    
    synopses_data = get_all_synopses(csv_path=get_dataset_csv_path(interactive=True), limit=MAX_DATASET)
    anime_docs = []
    titles = []
    synopses = []
    
    # prepara os docs, como handle_episodes ta false, e o dataset é gigantesco, usa apenas a sinopse. q ta no proprio csv e nao pesquisa nada na api
    # pra evitar muitas chamadas desnecessarias e demorar mto
    for entry in synopses_data:
        titles.append(entry['title'])
        synopses.append(entry['synopsis'])
        doc_tokens = await transformer.create_doc(entry['anime_id'], entry['title'], handle_episodes=False, dataset_synopsis=entry['synopsis'])
        anime_docs.append(doc_tokens)
    
    chosen_doc = await transformer.create_doc(selected_id, selected_title, handle_episodes=True)
    
    # aqui ele vetoriza tudo e calcula as similaridades usando o transformer
    all_docs = [chosen_doc] + anime_docs
    tfidf_matrix = await transformer.transform(all_docs)
    base_vec = tfidf_matrix[0]
    similarities = []
    
    for idx, vec in enumerate(tfidf_matrix[1:]):
        sim = await transformer.cosine_similarity(base_vec, vec)
        # remove o proprio anime escolhido da lista de similares
        if titles[idx].strip().lower() != selected_title.strip().lower():
            similarities.append((idx, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    print("\r" + " " * 80 + "\r", end='')
    
    # top 10 similares
    top_n = min(10, len(similarities))
    print_header(f"🎯 TOP {top_n} ANIMES SIMILARES")
    print(f"{Fore.MAGENTA}  Comparados: {len(similarities)} animes de {len(synopses_data)}{Style.RESET_ALL}")
    print_separator()
    
    for rank, (idx, sim) in enumerate(similarities[:top_n], 1):
        # nivel 
        if sim >= 0.1:
            nivel = f"{Fore.GREEN}●●●{Style.RESET_ALL} Alta - {Fore.MAGENTA}{sim*100:.1f}%{Style.RESET_ALL}"
            bar = "█" * 15
        elif sim >= 0.08:
            nivel = f"{Fore.YELLOW}●●○{Style.RESET_ALL} Média - {Fore.MAGENTA}{sim*100:.1f}%{Style.RESET_ALL}"
            bar = "█" * 10 + "░" * 5
        else:
            nivel = f"{Fore.RED}●○○{Style.RESET_ALL} Baixa - {Fore.MAGENTA}{sim*100:.1f}%{Style.RESET_ALL}"
            bar = "█" * 5 + "░" * 10
        
        print(f"\n{Fore.CYAN}  #{rank}{Style.RESET_ALL} {Fore.WHITE}{titles[idx]}{Style.RESET_ALL}")
        print(f"      {nivel} │ {Fore.MAGENTA}{sim:.3f}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}[{bar}]{Style.RESET_ALL}")
        
        synopsis_preview = synopses[idx][:300] + ('...' if len(synopses[idx]) > 300 else '')
        print(f"      {Fore.LIGHTBLACK_EX}{synopsis_preview}{Style.RESET_ALL}")
    
    print()
    await transformer.close_client()

def print_welcome():
    ascii_art = r'''⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⠟⠉⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠙⢻⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⣠⣄⠀⢻⣿⣿⣿⣿⣿⡿⠀⣠⣄⠀⠀⠀⢻⣿⣿⣏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⠀⠀⠀⠀⠰⣿⣿⠀⢸⣿⣿⣿⣿⣿⡇⠀⣿⣿⡇⠀⠀⢸⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠙⠃⠀⣼⣿⣿⣿⣿⣿⣇⠀⠙⠛⠁⠀⠀⣼⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣷⣤⣄⣀⣠⣤⣾⣿⣿⣿⣿⣽⣿⣿⣦⣄⣀⣀⣤⣾⣿⣿⣿⣿⠃⠀⠀⢀⣀⠀⠀
⠰⡶⠶⠶⠶⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠛⠉⠉⠙⠛⠋⠀
⠀⠀⢀⣀⣠⣤⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠷⠶⠶⠶⢤⣤⣀⠀
⠀⠛⠋⠉⠁⠀⣀⣴⡿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣤⣀⡀⠀⠀⠀⠀⠘⠃
⠀⠀⢀⣤⡶⠟⠉⠁⠀⠀⠉⠛⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠟⠉⠀⠀⠀⠉⠙⠳⠶⣄⡀⠀⠀
⠀⠀⠙⠁⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
'''
    print(Fore.CYAN + ascii_art + Style.RESET_ALL)
    print(f"{Fore.GREEN}🌌 Welcome to Kori! Your personal guide to the world of anime\n{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())
