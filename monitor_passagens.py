"""
✈️ Monitor de Passagens PRO — Com Botões Interativos
FlightAPI.io + Telegram Inline Keyboards
"""
 
import os, json, time, threading, requests, schedule
from datetime import datetime, timedelta
from copy import deepcopy
 
# ============================================================
#  CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "8684505587:AAGddTQdvwKbs9hf6FBwzw-VAHJOq9XdFik")
FLIGHTAPI_KEY   = os.getenv("FLIGHTAPI_KEY",  "69e079d51922a8f332a21d3d")
ADMIN_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID","1680681945")
DATA_FILE       = os.getenv("DATA_FILE",       "users.json")
VERIFICAR_HORAS = int(os.getenv("VERIFICAR_HORAS", "12"))
QUEDA_PERC      = 10
 
TELEGRAM_API      = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
USUARIOS_INICIAIS = ["1680681945", "6170699300", "5938670130"]
 
# ============================================================
#  DESTINOS
# ============================================================
ORIGENS_BRASIL = {
    "GRU": "São Paulo (GRU) 🇧🇷",
    "GIG": "Rio de Janeiro (GIG) 🇧🇷",
    "CNF": "Belo Horizonte (CNF) 🇧🇷",
    "SSA": "Salvador (SSA) 🇧🇷",
    "REC": "Recife (REC) 🇧🇷",
    "FOR": "Fortaleza (FOR) 🇧🇷",
    "CWB": "Curitiba (CWB) 🇧🇷",
    "POA": "Porto Alegre (POA) 🇧🇷",
    "BSB": "Brasília (BSB) 🇧🇷",
    "MAO": "Manaus (MAO) 🇧🇷",
    "BEL": "Belém (BEL) 🇧🇷",
    "FLN": "Florianópolis (FLN) 🇧🇷",
    "NAT": "Natal (NAT) 🇧🇷",
    "MCZ": "Maceió (MCZ) 🇧🇷",
}
 
DESTINOS_BRASIL = {
    "GRU": "São Paulo (GRU) 🇧🇷",
    "GIG": "Rio de Janeiro (GIG) 🇧🇷",
    "CNF": "Belo Horizonte (CNF) 🇧🇷",
    "SSA": "Salvador (SSA) 🇧🇷",
    "REC": "Recife (REC) 🇧🇷",
    "FOR": "Fortaleza (FOR) 🇧🇷",
    "CWB": "Curitiba (CWB) 🇧🇷",
    "POA": "Porto Alegre / Gramado 🇧🇷",
    "FLN": "Florianópolis (FLN) 🇧🇷",
    "NAT": "Natal (NAT) 🇧🇷",
    "MCZ": "Maceió (MCZ) 🇧🇷",
    "BEL": "Belém (BEL) 🇧🇷",
    "MAO": "Manaus (MAO) 🇧🇷",
    "IGU": "Foz do Iguaçu (IGU) 🇧🇷",
    "VCP": "Campinas (VCP) 🇧🇷",
}
 
DESTINOS_MUNDO = {
    "DUB": "Dublin 🇮🇪",
    "LIS": "Lisboa 🇵🇹",
    "MAD": "Madri 🇪🇸",
    "LHR": "Londres 🇬🇧",
    "CDG": "Paris 🇫🇷",
    "FCO": "Roma 🇮🇹",
    "AMS": "Amsterdã 🇳🇱",
    "FRA": "Frankfurt 🇩🇪",
    "BCN": "Barcelona 🇪🇸",
    "VIE": "Viena 🇦🇹",
    "PRG": "Praga 🇨🇿",
    "ATH": "Atenas 🇬🇷",
    "IST": "Istambul 🇹🇷",
    "ARN": "Estocolmo 🇸🇪",
    "HEL": "Helsinki 🇫🇮",
    "CPH": "Copenhague 🇩🇰",
    "WAW": "Varsóvia 🇵🇱",
    "BUD": "Budapeste 🇭🇺",
    "MIA": "Miami 🇺🇸",
    "JFK": "Nova York 🇺🇸",
    "LAX": "Los Angeles 🇺🇸",
    "ORD": "Chicago 🇺🇸",
    "EZE": "Buenos Aires 🇦🇷",
    "SCL": "Santiago 🇨🇱",
    "LIM": "Lima 🇵🇪",
    "BOG": "Bogotá 🇨🇴",
    "MEX": "Cidade do México 🇲🇽",
    "PTY": "Cidade do Panamá 🇵🇦",
    "CUN": "Cancún 🇲🇽",
    "DXB": "Dubai 🇦🇪",
    "NRT": "Tóquio 🇯🇵",
    "BKK": "Bangkok 🇹🇭",
    "SIN": "Singapura 🇸🇬",
    "ICN": "Seul 🇰🇷",
    "SYD": "Sydney 🇦🇺",
    "JNB": "Joanesburgo 🇿🇦",
    "CMN": "Casablanca 🇲🇦",
}
 
TODOS_DESTINOS = {**DESTINOS_BRASIL, **DESTINOS_MUNDO}
 
# ============================================================
#  PERSISTÊNCIA
# ============================================================
data_lock = threading.RLock()
state = {"users": {}, "historico_semana": []}
 
 
def carregar():
    global state
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                state.setdefault("users", {})
                state.setdefault("historico_semana", [])
        except Exception as e:
            print(f"⚠️ Erro ao carregar: {e}")
    for cid in USUARIOS_INICIAIS:
        if cid not in state["users"]:
            state["users"][cid] = novo_usuario(cid)
    salvar()
 
 
def salvar():
    with data_lock:
        try:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DATA_FILE)
        except Exception as e:
            print(f"⚠️ Erro ao salvar: {e}")
 
 
def novo_usuario(chat_id, nome=""):
    return {
        "chat_id":      str(chat_id),
        "nome":         nome,
        "origem":       "GRU",
        "destinos":     ["DUB", "LIS", "MIA", "EZE", "SCL"],
        "favorito":     "DUB",
        "preco_max":    5000,
        "data_ida":     "",
        "data_volta":   "",
        "classe":       "Economy",
        "adultos":      1,
        "pausado":      False,
        "ultimo_preco": {},
        "estado":       None,
        "criado_em":    datetime.now().isoformat(timespec="seconds"),
    }
 
 
def get_user(chat_id, nome=""):
    cid = str(chat_id)
    with data_lock:
        if cid not in state["users"]:
            state["users"][cid] = novo_usuario(cid, nome)
            salvar()
        return state["users"][cid]
 
 
# ============================================================
#  TELEGRAM
# ============================================================
 
def send(chat_id, texto, teclado=None, editar_msg_id=None):
    headers = {"Content-Type": "application/json"}
    payload = {
        "chat_id":    str(chat_id),
        "text":       texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if teclado:
        payload["reply_markup"] = {"inline_keyboard": teclado}
 
    if editar_msg_id:
        url = f"{TELEGRAM_API}/editMessageText"
        payload["message_id"] = editar_msg_id
    else:
        url = f"{TELEGRAM_API}/sendMessage"
 
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if r.status_code == 200:
            return data.get("result", {}).get("message_id")
        print(f"❌ send {chat_id}: {r.text[:200]}")
    except Exception as e:
        print(f"❌ send error: {e}")
    return None
 
 
def answer_callback(callback_id, texto=""):
    try:
        requests.post(f"{TELEGRAM_API}/answerCallbackQuery",
                      json={"callback_query_id": callback_id, "text": texto},
                      timeout=10)
    except:
        pass
 
 
# ============================================================
#  TECLADOS
# ============================================================
 
def teclado_menu_principal(usuario):
    origem_nome = ORIGENS_BRASIL.get(usuario["origem"], usuario["origem"])
    destinos_str = f"{len(usuario['destinos'])} destino(s)"
    data_ida  = usuario.get("data_ida")  or "Não definida"
    data_volta = usuario.get("data_volta") or "Somente ida"
    status = "⏸ Pausado" if usuario.get("pausado") else "▶️ Ativo"
 
    texto = (
        f"✈️ <b>Monitor de Passagens PRO</b>\n\n"
        f"👤 Olá, <b>{usuario.get('nome') or 'Viajante'}</b>!\n\n"
        f"⚙️ <b>Suas configurações:</b>\n"
        f"🛫 Origem: <b>{origem_nome}</b>\n"
        f"🌍 Destinos: <b>{destinos_str}</b>\n"
        f"📅 Ida: <b>{data_ida}</b>\n"
        f"📅 Volta: <b>{data_volta}</b>\n"
        f"💰 Preço máx: <b>R$ {usuario['preco_max']:,}</b>\n"
        f"💺 Classe: <b>{usuario.get('classe','Economy')}</b>\n"
        f"👥 Adultos: <b>{usuario.get('adultos',1)}</b>\n"
        f"🔔 Status: <b>{status}</b>\n\n"
        f"O que deseja fazer?"
    )
    botoes = [
        [
            {"text": "🔍 Buscar Agora",         "callback_data": "buscar"},
            {"text": "🌍 Meus Destinos",         "callback_data": "menu_destinos"},
        ],
        [
            {"text": "🛫 Mudar Origem",          "callback_data": "menu_origem"},
            {"text": "📅 Definir Datas",         "callback_data": "menu_datas"},
        ],
        [
            {"text": "💰 Preço Máximo",          "callback_data": "menu_preco"},
            {"text": "💺 Classe do Voo",         "callback_data": "menu_classe"},
        ],
        [
            {"text": "👥 Passageiros",           "callback_data": "menu_adultos"},
            {"text": "⭐ Destino Favorito",       "callback_data": "menu_favorito"},
        ],
        [
            {"text": "⏸ Pausar" if not usuario.get("pausado") else "▶️ Retomar",
             "callback_data": "toggle_pausa"},
            {"text": "📊 Resumo Semanal",        "callback_data": "resumo"},
        ],
    ]
    return texto, botoes
 
 
def teclado_origens():
    botoes = []
    items = list(ORIGENS_BRASIL.items())
    for i in range(0, len(items), 2):
        linha = []
        for cod, nome in items[i:i+2]:
            linha.append({"text": nome, "callback_data": f"set_origem_{cod}"})
        botoes.append(linha)
    botoes.append([{"text": "🔙 Voltar ao Menu", "callback_data": "menu_principal"}])
    return "🛫 <b>Selecione sua cidade de origem:</b>", botoes
 
 
def teclado_destinos_menu(usuario):
    ativos = "\n".join([f"  • {TODOS_DESTINOS.get(d, d)}" for d in usuario["destinos"]]) or "  Nenhum"
    texto = f"🌍 <b>Seus destinos ativos:</b>\n{ativos}\n\nO que deseja fazer?"
    botoes = [
        [
            {"text": "➕ Adicionar Brasil",       "callback_data": "add_dest_brasil_0"},
            {"text": "➕ Adicionar Internacional","callback_data": "add_dest_mundo_0"},
        ],
        [{"text": "❌ Remover Destinos",          "callback_data": "rem_dest_lista"}],
        [{"text": "🔙 Voltar ao Menu",            "callback_data": "menu_principal"}],
    ]
    return texto, botoes
 
 
def teclado_lista_adicionar(categoria, usuario, pagina=0):
    """Lista para ADICIONAR destinos — clica para toggle, Voltar retorna ao menu_destinos."""
    fonte = DESTINOS_BRASIL if categoria == "brasil" else DESTINOS_MUNDO
    titulo = "🇧🇷 <b>Adicionar destinos no Brasil:</b>" if categoria == "brasil" else "🌍 <b>Adicionar destinos internacionais:</b>"
    titulo += "\n✅ = já ativo | Toque para ativar/desativar"
 
    items = list(fonte.items())
    por_pagina = 8
    inicio = pagina * por_pagina
    fim = inicio + por_pagina
    pagina_items = items[inicio:fim]
 
    botoes = []
    for i in range(0, len(pagina_items), 2):
        linha = []
        for cod, nome in pagina_items[i:i+2]:
            marca = "✅ " if cod in usuario["destinos"] else ""
            linha.append({"text": f"{marca}{nome}", "callback_data": f"toggle_add_{categoria}_{pagina}_{cod}"})
        botoes.append(linha)
 
    nav = []
    if pagina > 0:
        nav.append({"text": "◀️ Anterior", "callback_data": f"add_dest_{categoria}_{pagina-1}"})
    if fim < len(items):
        nav.append({"text": "Próxima ▶️", "callback_data": f"add_dest_{categoria}_{pagina+1}"})
    if nav:
        botoes.append(nav)
 
    botoes.append([{"text": "✅ Concluído", "callback_data": "menu_destinos"}])
    return titulo, botoes
 
 
def teclado_lista_remover(usuario):
    """Lista para REMOVER destinos — clica para toggle, Voltar retorna ao menu_destinos."""
    if not usuario["destinos"]:
        return "⚠️ <b>Você não tem destinos ativos.</b>", [
            [{"text": "🔙 Voltar", "callback_data": "menu_destinos"}]
        ]
 
    texto = "❌ <b>Selecione os destinos para remover:</b>\nToque para marcar/desmarcar. Clique em Concluído quando terminar."
    botoes = []
    for cod in usuario["destinos"]:
        nome = TODOS_DESTINOS.get(cod, cod)
        botoes.append([{"text": f"❌ {nome}", "callback_data": f"toggle_rem_{cod}"}])
    botoes.append([{"text": "✅ Concluído", "callback_data": "menu_destinos"}])
    return texto, botoes
 
 
def teclado_datas(usuario):
    hoje = datetime.today()
    opcoes = []
    for semanas in [4, 6, 8, 10, 12, 16, 20, 24]:
        data = hoje + timedelta(weeks=semanas)
        label = data.strftime("%d/%m/%Y")
        valor = data.strftime("%Y-%m-%d")
        opcoes.append((label, valor))
 
    botoes = []
    for i in range(0, len(opcoes), 3):
        linha = []
        for label, valor in opcoes[i:i+3]:
            linha.append({"text": label, "callback_data": f"set_ida_{valor}"})
        botoes.append(linha)
    botoes.append([{"text": "📝 Digitar data manualmente", "callback_data": "digitar_data_ida"}])
    botoes.append([{"text": "🔙 Voltar ao Menu",           "callback_data": "menu_principal"}])
 
    data_atual = usuario.get("data_ida") or "não definida"
    texto = f"📅 <b>Selecione a data de ida:</b>\nAtual: <b>{data_atual}</b>\n\nEscolha ou digite:"
    return texto, botoes
 
 
def teclado_volta(data_ida_str):
    ida = datetime.strptime(data_ida_str, "%Y-%m-%d")
    opcoes = [(f"{d} dias ({(ida+timedelta(days=d)).strftime('%d/%m/%Y')})",
               (ida+timedelta(days=d)).strftime("%Y-%m-%d"))
              for d in [7, 10, 14, 21, 30]]
 
    botoes = [[{"text": label, "callback_data": f"set_volta_{valor}"}] for label, valor in opcoes]
    botoes.append([{"text": "📝 Digitar data manualmente", "callback_data": "digitar_data_volta"}])
    botoes.append([{"text": "🚫 Somente ida (sem volta)",  "callback_data": "set_volta_none"}])
    botoes.append([{"text": "🔙 Voltar",                   "callback_data": "menu_datas"}])
 
    texto = f"📅 <b>Ida:</b> {ida.strftime('%d/%m/%Y')}\n\n<b>Escolha a duração da viagem:</b>"
    return texto, botoes
 
 
def teclado_preco():
    opcoes = [
        ("R$ 1.000", 1000), ("R$ 2.000", 2000), ("R$ 3.000", 3000),
        ("R$ 4.000", 4000), ("R$ 5.000", 5000), ("R$ 7.000", 7000),
        ("R$ 10.000",10000),("R$ 15.000",15000), ("R$ 20.000",20000),
    ]
    botoes = []
    for i in range(0, len(opcoes), 3):
        linha = [{"text": l, "callback_data": f"set_preco_{v}"} for l, v in opcoes[i:i+3]]
        botoes.append(linha)
    botoes.append([{"text": "📝 Digitar valor",    "callback_data": "digitar_preco"}])
    botoes.append([{"text": "🔙 Voltar ao Menu",   "callback_data": "menu_principal"}])
    return "💰 <b>Preço máximo por pessoa (ida e volta):</b>", botoes
 
 
def teclado_classe():
    botoes = [
        [
            {"text": "💺 Econômica",         "callback_data": "set_classe_Economy"},
            {"text": "🥈 Premium Economy",   "callback_data": "set_classe_Premium_Economy"},
        ],
        [
            {"text": "🥇 Executiva",         "callback_data": "set_classe_Business"},
            {"text": "👑 Primeira Classe",   "callback_data": "set_classe_First"},
        ],
        [{"text": "🔙 Voltar ao Menu",       "callback_data": "menu_principal"}],
    ]
    return "💺 <b>Selecione a classe do voo:</b>", botoes
 
 
def teclado_adultos():
    botoes = [
        [
            {"text": "👤 1",  "callback_data": "set_adultos_1"},
            {"text": "👥 2",  "callback_data": "set_adultos_2"},
            {"text": "👨‍👩‍👧 3","callback_data": "set_adultos_3"},
        ],
        [
            {"text": "4️⃣ 4", "callback_data": "set_adultos_4"},
            {"text": "5️⃣ 5", "callback_data": "set_adultos_5"},
            {"text": "6️⃣ 6", "callback_data": "set_adultos_6"},
        ],
        [{"text": "🔙 Voltar ao Menu", "callback_data": "menu_principal"}],
    ]
    return "👥 <b>Quantos adultos vão viajar?</b>", botoes
 
 
def teclado_favorito(usuario):
    botoes = []
    items = [(cod, TODOS_DESTINOS.get(cod, cod)) for cod in usuario["destinos"]]
    for i in range(0, len(items), 2):
        linha = []
        for cod, nome in items[i:i+2]:
            marca = "⭐ " if cod == usuario.get("favorito") else ""
            linha.append({"text": f"{marca}{nome}", "callback_data": f"set_fav_{cod}"})
        botoes.append(linha)
    botoes.append([{"text": "🔙 Voltar ao Menu", "callback_data": "menu_principal"}])
    return "⭐ <b>Selecione seu destino favorito:</b>", botoes
 
 
# ============================================================
#  FLIGHTAPI — BUSCA COM PARSING CORRETO
# ============================================================
 
def extrair_preco(dados):
    """
    Extrai o menor preço da resposta da FlightAPI.
    A API usa snake_case: pricing_options, leg_ids, items[].url
    """
    itinerarios = dados.get("itineraries") or []
    menor_preco = float("inf")
    melhor_link = ""
    melhor_leg_ida   = {}
    melhor_leg_volta = {}
 
    legs_map = {leg["id"]: leg for leg in (dados.get("legs") or [])}
 
    for itin in itinerarios:
        # API retorna snake_case: pricing_options
        pricing = itin.get("pricing_options") or itin.get("pricingOptions") or []
        if not pricing:
            continue
 
        preco_raw = pricing[0].get("price", {})
        if isinstance(preco_raw, dict):
            preco = float(preco_raw.get("amount", 0) or 0)
        else:
            preco = float(preco_raw or 0)
 
        if preco <= 0:
            continue
 
        if preco < menor_preco:
            menor_preco = preco
 
            # Link está dentro de items[0].url
            items = pricing[0].get("items") or []
            if items:
                url_path = items[0].get("url", "")
                # Monta link completo do Skyscanner
                melhor_link = f"https://www.skyscanner.com.br{url_path}" if url_path else ""
            else:
                melhor_link = pricing[0].get("deepLink", "") or pricing[0].get("deep_link", "")
 
            # leg_ids também em snake_case
            leg_ids = itin.get("leg_ids") or itin.get("legIds") or []
            if leg_ids:
                melhor_leg_ida = legs_map.get(leg_ids[0], {})
            if len(leg_ids) > 1:
                melhor_leg_volta = legs_map.get(leg_ids[1], {})
 
    if menor_preco == float("inf"):
        return None, None, None, None
 
    return menor_preco, melhor_link, melhor_leg_ida, melhor_leg_volta
 
 
def buscar_voo(origem, destino, data_ida, data_volta, adultos, classe):
    try:
        if data_volta:
            url = (
                f"https://api.flightapi.io/roundtrip/{FLIGHTAPI_KEY}"
                f"/{origem}/{destino}/{data_ida}/{data_volta}"
                f"/{adultos}/0/0/{classe}/BRL"
            )
        else:
            url = (
                f"https://api.flightapi.io/onewaytrip/{FLIGHTAPI_KEY}"
                f"/{origem}/{destino}/{data_ida}"
                f"/{adultos}/0/0/{classe}/BRL"
            )
 
        print(f"  🔍 {origem}→{destino} {data_ida}")
        r = requests.get(url, timeout=35)
        print(f"  📡 Status: {r.status_code}")
 
        if r.status_code == 410:
            print(f"  ⚠️ Sem voos {origem}→{destino}")
            return None
        if r.status_code != 200:
            print(f"  ❌ Erro {r.status_code}: {r.text[:200]}")
            return None
 
        dados = r.json()
 
        # DEBUG — mostra estrutura para diagnóstico
        chaves = list(dados.keys()) if isinstance(dados, dict) else type(dados).__name__
        print(f"  🔑 Chaves da resposta: {chaves}")
 
        preco, link, leg_ida, leg_volta = extrair_preco(dados)
 
        if preco is None:
            print(f"  😔 Nenhum itinerário com preço para {destino}")
            return None
 
        paradas = (leg_ida.get("stopovers_count") or leg_ida.get("stopoversCount") or 0) if leg_ida else 0
        duracao = (leg_ida.get("duration_in_minutes") or leg_ida.get("duration") or "—") if leg_ida else "—"
 
        print(f"  ✅ {destino}: R$ {preco:,.0f}")
        return {
            "origem":    origem,
            "destino":   destino,
            "preco":     preco,
            "data_ida":  data_ida,
            "data_volta": data_volta or "—",
            "paradas":   paradas,
            "duracao":   duracao,
            "link":      link,
            "classe":    classe,
            "adultos":   adultos,
        }
 
    except Exception as e:
        print(f"  ⚠️ Exceção em {destino}: {e}")
        return None
 
 
def fmt_resultado(oferta, fav=False):
    destino_nome = TODOS_DESTINOS.get(oferta["destino"], oferta["destino"])
    origem_nome  = ORIGENS_BRASIL.get(oferta["origem"], oferta["origem"])
    paradas = "Direto ✈️" if oferta["paradas"] == 0 else f"{oferta['paradas']} parada(s)"
    prefixo = "🌟 " if fav else ""
 
    msg = (
        f"{prefixo}<b>{destino_nome}</b>\n"
        f"   💵 <b>R$ {oferta['preco']:,.0f}</b> por pessoa\n"
        f"   🛫 {origem_nome}\n"
        f"   📅 Ida: {oferta['data_ida']}"
    )
    if oferta["data_volta"] != "—":
        msg += f" | Volta: {oferta['data_volta']}"
    msg += f"\n   ✈️ {paradas}"
    if oferta["duracao"] and oferta["duracao"] != "—":
        msg += f" | ⏱ {oferta['duracao']} min"
    msg += f" | 💺 {oferta['classe']}\n"
    if oferta.get("link"):
        msg += f"   🔗 <a href='{oferta['link']}'>Reservar agora</a>\n"
    return msg
 
 
# ============================================================
#  BUSCA PARA USUÁRIO
# ============================================================
 
def buscar_para_usuario(usuario):
    if not usuario.get("data_ida"):
        return None, "❌ Defina uma data de ida primeiro!"
 
    origem    = usuario.get("origem", "GRU")
    data_ida  = usuario["data_ida"]
    data_volta = usuario.get("data_volta") or ""
    adultos   = usuario.get("adultos", 1)
    classe    = usuario.get("classe", "Economy")
    preco_max = usuario.get("preco_max", 5000)
    favorito  = usuario.get("favorito")
 
    ofertas = []
    quedas  = []
 
    for destino in usuario.get("destinos", []):
        oferta = buscar_voo(origem, destino, data_ida, data_volta, adultos, classe)
        if not oferta:
            time.sleep(0.5)
            continue
 
        if oferta["preco"] <= preco_max:
            if destino == favorito:
                oferta["favorito"] = True
            ofertas.append(oferta)
 
            anterior = usuario.get("ultimo_preco", {}).get(destino)
            if anterior and anterior > 0:
                queda = (anterior - oferta["preco"]) / anterior * 100
                if queda >= QUEDA_PERC:
                    quedas.append({"oferta": oferta, "anterior": anterior, "perc": queda})
 
        time.sleep(1)
 
    with data_lock:
        usuario["ultimo_preco"] = {o["destino"]: o["preco"] for o in ofertas}
        salvar()
 
    return ofertas, quedas
 
 
def montar_msg_resultados(usuario, ofertas, quedas):
    if not ofertas:
        return (
            f"😔 <b>Nenhuma oferta encontrada</b>\n\n"
            f"Não encontrei passagens abaixo de R$ {usuario['preco_max']:,} "
            f"para as datas selecionadas.\n\n"
            f"💡 Dicas:\n"
            f"• Aumente o preço máximo\n"
            f"• Mude as datas da viagem\n"
            f"• Adicione mais destinos\n"
        )
 
    ofertas.sort(key=lambda x: x["preco"])
    fav   = next((o for o in ofertas if o.get("favorito")), None)
    outras = [o for o in ofertas if not o.get("favorito")]
 
    msg = (
        f"✈️ <b>RESULTADOS DA BUSCA</b>\n"
        f"🗓 {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
        f"💰 Até R$ {usuario['preco_max']:,} | {len(ofertas)} oferta(s)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
 
    if quedas:
        msg += "🔥 <b>QUEDA DE PREÇO!</b>\n"
        for q in quedas:
            nome = TODOS_DESTINOS.get(q["oferta"]["destino"], q["oferta"]["destino"])
            msg += (f"📉 {nome}: R$ {q['anterior']:,.0f} → "
                    f"<b>R$ {q['oferta']['preco']:,.0f}</b> (-{q['perc']:.0f}%)\n")
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
 
    if fav:
        msg += "⭐ <b>SEU FAVORITO</b>\n"
        msg += fmt_resultado(fav, fav=True) + "\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
 
    if outras:
        msg += f"🌍 <b>OUTRAS OFERTAS ({len(outras)})</b>\n\n"
        for o in outras[:8]:
            msg += fmt_resultado(o) + "\n"
        if len(outras) > 8:
            msg += f"<i>+{len(outras)-8} outras ofertas.</i>\n"
 
    msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Monitor Passagens PRO"
    return msg
 
 
# ============================================================
#  CALLBACKS (BOTÕES)
# ============================================================
 
def processar_callback(update):
    cb      = update.get("callback_query", {})
    if not cb:
        return
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    msg_id  = cb.get("message", {}).get("message_id")
    cb_id   = cb.get("id")
    data    = cb.get("data", "")
    nome    = cb.get("from", {}).get("first_name", "")
 
    if not chat_id:
        return
 
    answer_callback(cb_id)
    usuario = get_user(chat_id, nome)
 
    # MENU PRINCIPAL
    if data == "menu_principal":
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # ORIGEM
    elif data == "menu_origem":
        t, b = teclado_origens()
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("set_origem_"):
        cod = data[11:]
        usuario["origem"] = cod
        salvar()
        answer_callback(cb_id, f"✅ Origem: {ORIGENS_BRASIL.get(cod, cod)}")
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # DESTINOS — menu
    elif data == "menu_destinos":
        t, b = teclado_destinos_menu(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # DESTINOS — adicionar (com paginação)
    elif data.startswith("add_dest_brasil_"):
        pagina = int(data.split("_")[-1])
        t, b = teclado_lista_adicionar("brasil", usuario, pagina)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("add_dest_mundo_"):
        pagina = int(data.split("_")[-1])
        t, b = teclado_lista_adicionar("mundo", usuario, pagina)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # DESTINOS — toggle na lista de adicionar
    elif data.startswith("toggle_add_"):
        # formato: toggle_add_<categoria>_<pagina>_<cod>
        partes    = data.split("_", 4)
        categoria = partes[2]
        pagina    = int(partes[3])
        cod       = partes[4]
 
        if cod in usuario["destinos"]:
            usuario["destinos"].remove(cod)
            answer_callback(cb_id, f"❌ {TODOS_DESTINOS.get(cod, cod)} removido")
        else:
            usuario["destinos"].append(cod)
            answer_callback(cb_id, f"✅ {TODOS_DESTINOS.get(cod, cod)} adicionado")
        salvar()
 
        # Fica na mesma lista de adicionar
        t, b = teclado_lista_adicionar(categoria, usuario, pagina)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # DESTINOS — remover (lista com multi-seleção)
    elif data == "rem_dest_lista":
        t, b = teclado_lista_remover(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("toggle_rem_"):
        cod = data[11:]
        if cod in usuario["destinos"]:
            usuario["destinos"].remove(cod)
            answer_callback(cb_id, f"❌ {TODOS_DESTINOS.get(cod, cod)} removido")
        salvar()
        # Fica na tela de remover para continuar removendo
        t, b = teclado_lista_remover(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # DATAS
    elif data == "menu_datas":
        t, b = teclado_datas(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("set_ida_"):
        data_ida = data[8:]
        usuario["data_ida"]  = data_ida
        usuario["data_volta"] = ""
        salvar()
        t, b = teclado_volta(data_ida)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data == "digitar_data_ida":
        usuario["estado"] = "aguardando_data_ida"
        salvar()
        send(chat_id, "📅 <b>Digite a data de ida:</b>\nFormato: <code>DD/MM/AAAA</code>\nEx: <code>15/07/2026</code>")
 
    elif data == "digitar_data_volta":
        usuario["estado"] = "aguardando_data_volta"
        salvar()
        send(chat_id, "📅 <b>Digite a data de volta:</b>\nFormato: <code>DD/MM/AAAA</code>\nEx: <code>29/07/2026</code>")
 
    elif data.startswith("set_volta_"):
        val = data[10:]
        usuario["data_volta"] = "" if val == "none" else val
        salvar()
        answer_callback(cb_id, "✅ Datas configuradas!")
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # PREÇO
    elif data == "menu_preco":
        t, b = teclado_preco()
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("set_preco_"):
        val = int(data[10:])
        usuario["preco_max"] = val
        salvar()
        answer_callback(cb_id, f"✅ Preço máx: R$ {val:,}")
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data == "digitar_preco":
        usuario["estado"] = "aguardando_preco"
        salvar()
        send(chat_id, "💰 <b>Digite o preço máximo em reais:</b>\nEx: <code>4500</code>")
 
    # CLASSE
    elif data == "menu_classe":
        t, b = teclado_classe()
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("set_classe_"):
        classe = data[11:]
        usuario["classe"] = classe
        salvar()
        nomes = {"Economy":"Econômica","Premium_Economy":"Premium Economy",
                 "Business":"Executiva","First":"Primeira Classe"}
        answer_callback(cb_id, f"✅ {nomes.get(classe, classe)}")
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # ADULTOS
    elif data == "menu_adultos":
        t, b = teclado_adultos()
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("set_adultos_"):
        n = int(data[12:])
        usuario["adultos"] = n
        salvar()
        answer_callback(cb_id, f"✅ {n} adulto(s)")
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # FAVORITO
    elif data == "menu_favorito":
        t, b = teclado_favorito(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    elif data.startswith("set_fav_"):
        cod = data[8:]
        usuario["favorito"] = cod
        salvar()
        answer_callback(cb_id, f"⭐ Favorito: {TODOS_DESTINOS.get(cod, cod)}")
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # PAUSAR/RETOMAR
    elif data == "toggle_pausa":
        usuario["pausado"] = not usuario.get("pausado", False)
        salvar()
        status = "⏸ Pausado" if usuario["pausado"] else "▶️ Retomado"
        answer_callback(cb_id, status)
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b, editar_msg_id=msg_id)
 
    # BUSCAR AGORA
    elif data == "buscar":
        if not usuario.get("data_ida"):
            send(chat_id,
                 "⚠️ <b>Defina uma data de ida primeiro!</b>",
                 [[{"text": "📅 Definir Data", "callback_data": "menu_datas"}]])
            return
        send(chat_id, "🔍 <b>Buscando as melhores passagens...</b>\nAguarde alguns segundos. ✈️")
        threading.Thread(target=_buscar_thread, args=(deepcopy(usuario),), daemon=True).start()
 
    # RESUMO SEMANAL
    elif data == "resumo":
        enviar_resumo_usuario(usuario)
 
 
def _buscar_thread(usuario):
    ofertas, quedas = buscar_para_usuario(usuario)
    if ofertas is None:
        send(usuario["chat_id"], quedas,
             [[{"text": "📅 Definir Data", "callback_data": "menu_datas"}]])
        return
    msg = montar_msg_resultados(usuario, ofertas, quedas)
    send(usuario["chat_id"], msg,
         [[{"text": "🔙 Voltar ao Menu", "callback_data": "menu_principal"}]])
 
 
# ============================================================
#  MENSAGENS DE TEXTO
# ============================================================
 
def processar_mensagem(update):
    msg     = update.get("message", {})
    if not msg:
        return
    chat    = msg.get("chat", {})
    chat_id = chat.get("id")
    texto   = (msg.get("text") or "").strip()
    nome    = chat.get("first_name", "")
 
    if not chat_id or not texto:
        return
 
    usuario = get_user(chat_id, nome)
    estado  = usuario.get("estado")
 
    if texto.lower() in ["/start", "/menu", "menu", "início", "inicio"]:
        usuario["nome"]   = nome
        usuario["estado"] = None
        salvar()
        t, b = teclado_menu_principal(usuario)
        send(chat_id, t, b)
        return
 
    if texto.lower() in ["/ajuda", "/help"]:
        send(chat_id,
             "✈️ <b>Como usar:</b>\n\n"
             "1️⃣ /start — abre o menu\n"
             "2️⃣ Configure <b>origem</b> e <b>destinos</b>\n"
             "3️⃣ Defina as <b>datas</b>\n"
             "4️⃣ Configure o <b>preço máximo</b>\n"
             "5️⃣ Toque em <b>Buscar Agora</b>!\n\n"
             f"O bot busca automaticamente a cada {VERIFICAR_HORAS}h. 🔔",
             [[{"text": "⚙️ Abrir Menu", "callback_data": "menu_principal"}]])
        return
 
    # Estados aguardando input
    if estado == "aguardando_data_ida":
        try:
            dt = datetime.strptime(texto.strip(), "%d/%m/%Y")
            if dt.date() <= datetime.today().date():
                send(chat_id, "⚠️ A data precisa ser no futuro! Tente novamente:")
                return
            usuario["data_ida"]  = dt.strftime("%Y-%m-%d")
            usuario["data_volta"] = ""
            usuario["estado"]    = None
            salvar()
            t, b = teclado_volta(usuario["data_ida"])
            send(chat_id, t, b)
        except ValueError:
            send(chat_id, "⚠️ Formato inválido! Use <code>DD/MM/AAAA</code>\nEx: <code>15/07/2026</code>")
        return
 
    if estado == "aguardando_data_volta":
        try:
            dt  = datetime.strptime(texto.strip(), "%d/%m/%Y")
            ida = datetime.strptime(usuario["data_ida"], "%Y-%m-%d")
            if dt.date() <= ida.date():
                send(chat_id, "⚠️ A volta precisa ser depois da ida! Tente novamente:")
                return
            usuario["data_volta"] = dt.strftime("%Y-%m-%d")
            usuario["estado"]     = None
            salvar()
            answer_callback("", "")
            t, b = teclado_menu_principal(usuario)
            send(chat_id, "✅ Datas configuradas!\n\n" + t, b)
        except ValueError:
            send(chat_id, "⚠️ Formato inválido! Use <code>DD/MM/AAAA</code>\nEx: <code>29/07/2026</code>")
        return
 
    if estado == "aguardando_preco":
        try:
            val = int(texto.strip().replace(".", "").replace(",", "").replace("R$","").strip())
            if val < 100:
                send(chat_id, "⚠️ Valor muito baixo! Tente um valor maior:")
                return
            usuario["preco_max"] = val
            usuario["estado"]    = None
            salvar()
            t, b = teclado_menu_principal(usuario)
            send(chat_id, f"✅ Preço máximo: R$ {val:,}\n\n" + t, b)
        except ValueError:
            send(chat_id, "⚠️ Só números! Ex: <code>4500</code>")
        return
 
    # Qualquer outra mensagem → abre menu
    t, b = teclado_menu_principal(usuario)
    send(chat_id, t, b)
 
 
# ============================================================
#  VERIFICAÇÃO AUTOMÁTICA
# ============================================================
 
def verificar_automatico():
    print(f"\n[{datetime.now()}] 🔍 Verificação automática...")
    with data_lock:
        usuarios = [deepcopy(u) for u in state["users"].values()
                    if not u.get("pausado") and u.get("data_ida")]
 
    for usuario in usuarios:
        try:
            with data_lock:
                vivo = state["users"].get(usuario["chat_id"])
                if not vivo:
                    continue
            ofertas, quedas = buscar_para_usuario(vivo)
            if ofertas is None:
                continue
            if ofertas:
                msg = montar_msg_resultados(vivo, ofertas, quedas)
                send(vivo["chat_id"], msg,
                     [[{"text": "⚙️ Configurações", "callback_data": "menu_principal"}]])
            else:
                send(vivo["chat_id"],
                     f"🔍 <i>Verificação automática: nenhuma oferta abaixo de "
                     f"R$ {vivo['preco_max']:,} no momento.</i>")
        except Exception as e:
            print(f"⚠️ Erro {usuario['chat_id']}: {e}")
 
 
def enviar_resumo_usuario(usuario):
    with data_lock:
        historico = [e for e in state.get("historico_semana", [])
                     if e.get("chat_id") == usuario["chat_id"]]
 
    if not historico:
        send(usuario["chat_id"],
             "📅 <b>Resumo Semanal</b>\n\nNenhuma busca esta semana.",
             [[{"text": "⚙️ Abrir Menu", "callback_data": "menu_principal"}]])
        return
 
    melhores = {}
    for entry in historico:
        for o in entry.get("ofertas", []):
            k = o["destino"]
            if k not in melhores or o["preco"] < melhores[k]["preco"]:
                melhores[k] = o
 
    ranking = sorted(melhores.values(), key=lambda x: x["preco"])[:10]
    msg = (
        f"📅 <b>RESUMO SEMANAL</b>\n"
        f"🗓 {datetime.now().strftime('%d/%m/%Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for i, o in enumerate(ranking, 1):
        msg += f"<b>#{i}</b> {fmt_resultado(o)}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Monitor Passagens PRO"
    send(usuario["chat_id"], msg,
         [[{"text": "⚙️ Voltar ao Menu", "callback_data": "menu_principal"}]])
 
 
def resumo_semanal_todos():
    with data_lock:
        usuarios = list(state["users"].values())
    for u in usuarios:
        if not u.get("pausado"):
            enviar_resumo_usuario(u)
    with data_lock:
        state["historico_semana"] = []
        salvar()
 
 
# ============================================================
#  POLLING
# ============================================================
 
def polling():
    print(f"[{datetime.now()}] 📡 Polling iniciado...")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=40)
            if r.status_code != 200:
                time.sleep(5)
                continue
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                try:
                    if "callback_query" in upd:
                        processar_callback(upd)
                    elif "message" in upd:
                        processar_mensagem(upd)
                except Exception as e:
                    print(f"⚠️ Update error: {e}")
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            print(f"⚠️ Polling: {e}")
            time.sleep(5)
 
 
def scheduler_loop():
    schedule.every(VERIFICAR_HORAS).hours.do(verificar_automatico)
    schedule.every().sunday.at("09:00").do(resumo_semanal_todos)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"⚠️ Scheduler: {e}")
        time.sleep(30)
 
 
# ============================================================
#  INÍCIO
# ============================================================
 
def main():
    print("=" * 60)
    print("✈️  Monitor de Passagens PRO — v3 com Botões")
    print(f"    {len(TODOS_DESTINOS)} destinos | FlightAPI.io")
    print("=" * 60)
 
    carregar()
 
    send(ADMIN_CHAT_ID,
         "🚀 <b>Monitor PRO v3 online!</b>\n\n"
         f"✨ Botões interativos\n"
         f"🌍 {len(TODOS_DESTINOS)} destinos\n"
         f"🇧🇷 Cidades brasileiras incluídas\n"
         f"🔧 Remoção múltipla de destinos\n"
         f"⏰ Verificação a cada {VERIFICAR_HORAS}h\n\n"
         "Use /start para abrir o menu! ✈️")
 
    threading.Thread(target=scheduler_loop, daemon=True).start()
    polling()
 
 
if __name__ == "__main__":
    main()
