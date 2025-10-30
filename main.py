import asyncio
from src.transformer.transformer import Transformer
from src.api.anilist import AniListClient
from src.api.anizip import AniZipClient
from src.searcher.find import remove_html_tags

async def main():
    print_welcome()
    try:
        anime_title = input("Digite o nome do anime para pesquisar: ")
        await search_anime_api(anime_title)
    finally:
        print("Fechando cliente AniList...")
        
async def search_anime_api(title: str, limit: int = 10):
    """search animes in anilist by title, with interactive pagination."""
    import textwrap
    client = AniListClient()
    page = 1
    while True:
        results, total_pages = await client.search(title, limit=limit, page=page)
        for anime in results:
            anime['description'] = remove_html_tags(anime['description'] or '')
        if not results:
            msg = f"❌ Nenhum anime encontrado para '{title}'." if page == 1 else "❌ Nenhum resultado nesta página."
            print(msg)
            return
        header = f"🔎 Resultados para '{title}'    (Página {page}/{total_pages})"
        print('\n' + header)
        print("="*60)
        for idx, anime in enumerate(results):
            print(f"[{idx}] {anime['title_romaji'] or anime['title_english'] or anime['title_native']}")
            print(f"Episódios: {anime['episodes']} | Nota: {anime['average_score']}")
            desc = anime['description']
            desc_preview = textwrap.shorten(desc.replace('\n', ' '), width=60, placeholder='...')
            print(f"Sinopse: {desc_preview}")
            print("-"*60)
        print(f"Página {page} de {total_pages}")
        print("[n] Próxima página | [p] Página anterior | [ENTER] Cancelar")
        escolha = input(f"Digite o número do anime para ver detalhes (0-{len(results)-1}), ou comando: ")
        if escolha == '':
            print("Cancelado.")
            break
        if escolha.lower() == 'n':
            if page < total_pages:
                page += 1
            else:
                print("Já está na última página.")
            continue
        if escolha.lower() == 'p':
            if page > 1:
                page -= 1
            else:
                print("Já está na primeira página.")
            continue
        if escolha.isdigit() and 0 <= int(escolha) < len(results):
            idx = int(escolha)
            anime = results[idx]
            print('\n' + "="*30 + " Detalhes do Anime " + "="*30)
            print(f"ID: {anime['id']}")
            print(f"Título (romaji): {anime['title_romaji']}")
            print(f"Título (english): {anime['title_english']}")
            print(f"Título (native): {anime['title_native']}")
            print(f"Episódios: {anime['episodes']}")
            print(f"Nota média: {anime['average_score']}")
            print("Sinopse:")
            print(textwrap.fill(anime['description'], width=60))
            print("="*80)
            while True:
                acao = input("Digite [s] para ver animes similares, [e] para ver episódios, ou ENTER para voltar: ").strip().lower()
                if acao == 's':
                    selected_title = anime.get('title_romaji') or anime.get('title_english') or anime.get('title_native')
                    selected_id = anime.get('id')
                    await show_similar_animes(selected_title, selected_id)
                    break
                elif acao == 'e':
                    await show_anime_episodes(anime['id'])
                    break
                elif acao == '':
                    break
                else:
                    print("Opção inválida. Tente novamente.")
            break
        else:
            print("Opção inválida. Tente novamente.")
    await client.close()

async def show_anime_episodes(anilist_id: int):
    """search and show regular episodes of the anime by anilist_id using AniZipClient and extract_all_episodes_info."""
    client = AniZipClient()
    try:
        response = await client.get_mappings(anilist_id)
        episodes_data = response.get('episodes', {})
        if not episodes_data:
            print("Nenhum episódio encontrado para este anime.")
            return
        episodes = client.extract_all_episodes_info(episodes_data, anilist_id)
        if not episodes:
            print("Nenhum episódio regular encontrado para este anime.")
            return
        print("\nEpisódios regulares encontrados:")
        print("="*60)
        for ep in episodes:
            print(f"Episódio {ep['episode_number']}: {ep['episode_title']}")
            summary = ep.get('synopsis') or ''
            if summary:
                print(f"{summary[:60]}{'...' if len(summary) > 60 else ''}")
            print("-"*60)
        print()
    except Exception as e:
        print(f"Erro ao buscar episódios: {e}")
    finally:
        await client.close()

async def show_similar_animes(selected_title: str, selected_id: int):
    """show the most similar animes to the selected title using the Transformer."""
    from src.transformer.transformer import Transformer
    from src.constants.cleaner import get_all_synopses
    transformer = Transformer()
    # usa um limite maximo de 500 animes do dataset, pra evitar travamentos e demora
    # vou dar um jeito de deixar customizavel isso depois
    MAX_DATASET = 500
    print(f"Comparando com no máximo {MAX_DATASET} animes do dataset para evitar travamentos.")
    synopses_data = get_all_synopses(csv_path="D:/alves/recommendation-sys/src/constants/dataset.csv", limit=MAX_DATASET)
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

    # cria o doc do anime escolhido, esse o handle_episodes ta true, entao ele pesquisa na api os episodios e tal
    # o doc é criado usando sinopse geral do anime + sinopse dos episodios, se tiver. fiz isso so pra ter um pouquinho mais de exatidao 
    chosen_doc = await transformer.create_doc(selected_id, selected_title, handle_episodes=True)

    # aqui ele vetoriza tudo e calcula as similaridades usando o transformer
    all_docs = [chosen_doc] + anime_docs
    tfidf_matrix = await transformer.transform(all_docs)
    base_vec = tfidf_matrix[0]
    similarities = []
    for idx, vec in enumerate(tfidf_matrix[1:]):
        sim = await transformer.cosine_similarity(base_vec, vec)
        # remove o proprio anime escolhido da lista de similares
        if titles[idx].strip().lower() == selected_title.strip().lower():
            continue
        similarities.append((idx, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_n = 10 if len(similarities) > 10 else len(similarities)
    print(f"\nTop {top_n} animes mais similares (comparados: {len(similarities)} de {len(synopses_data)}):")
    for idx, sim in similarities[:top_n]:
        if sim >= 0.1:
            nivel = "Alta"
        elif sim >= 0.08:
            nivel = "Média"
        else:
            nivel = "Baixa"
        print(f"Título: {titles[idx]} | Similaridade: {sim:.3f} ({nivel})")
        print(f"Sinopse: {synopses[idx][:300]}...\n")
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
⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⠟⠉⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠙⢻⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⣠⣄⠀⢻⣿⣿⣿⣿⣿⡿⠀⣠⣄⠀⠀⠀⢻⣿⣿⣏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⠀⠀⠀⠀⠰⣿⣿⠀⢸⣿⣿⣿⣿⣿⡇⠀⣿⣿⡇⠀⠀⢸⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠙⠃⠀⣼⣿⣿⣿⣿⣿⣇⠀⠙⠛⠁⠀⠀⣼⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣷⣤⣄⣀⣠⣤⣾⣿⣿⣿⣿⣽⣿⣿⣦⣄⣀⣀⣤⣾⣿⣿⣿⣿⠃⠀⠀⢀⣀⠀⠀
⠰⡶⠶⠶⠶⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠛⠉⠉⠙⠛⠋⠀
⠀⠀⢀⣀⣠⣤⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠷⠶⠶⠶⢤⣤⣀⠀
⠀⠛⠋⠉⠁⠀⣀⣴⡿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣤⣀⡀⠀⠀⠀⠀⠘⠃
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
    print(ascii_art)
    print("Welcome to Kori! Your personal guide to the world of anime\n")

if __name__ == "__main__":
    asyncio.run(main())
