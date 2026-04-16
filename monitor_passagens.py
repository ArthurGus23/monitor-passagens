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
QUEDA_PERC      = 10   # % de queda para alertar
 
TELEGRAM_API    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
USUARIOS_INICIAIS = ["1680681945", "6170699300", "5938670130"]
 
# ============================================================
#  DESTINOS — BRASIL + MUNDO
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
    "VCP": "Campinas (VCP) 🇧🇷",
    "MCZ": "Maceió (MCZ) 🇧🇷",
    "NAT": "Natal (NAT) 🇧🇷",
}
 
DESTINOS_BRASIL = {
    "GRU": "São Paulo (GRU) 🇧🇷",
    "GIG": "Rio de Janeiro (GIG) 🇧🇷",
    "CNF": "Belo Horizonte (CNF) 🇧🇷",
    "SSA": "Salvador (SSA) 🇧🇷",
    "REC": "Recife (REC) 🇧🇷",
    "FOR": "Fortaleza (FOR) 🇧🇷",
    "CWB": "Curitiba (CWB) 🇧🇷",
    "POA": "Porto Alegre (POA) 🇧🇷",
    "FLN": "Florianópolis (FLN) 🇧🇷",
    "GRV": "Gramado/Canela* 🇧🇷",
    "NAT": "Natal (NAT) 🇧🇷",
    "MCZ": "Maceió (MCZ) 🇧🇷",
    "BEL": "Belém (BEL) 🇧🇷",
    "MAO": "Manaus (MAO) 🇧🇷",
    "IGU": "Foz do Iguaçu (IGU) 🇧🇷",
}
 
DESTINOS_MUNDO = {
    # Europa
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
    # Américas
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
    # Ásia/Oceania
    "DXB": "Dubai 🇦🇪",
    "NRT": "Tóquio 🇯🇵",
    "BKK": "Bangkok 🇹🇭",
    "SIN": "Singapura 🇸🇬",
    "ICN": "Seul 🇰🇷",
    "SYD": "Sydney 🇦🇺",
    # África
    "JNB": "Joanesburgo 🇿🇦",
    "CMN": "Casablanca 🇲🇦",
}
 
TODOS_DESTINOS = {**DESTINOS_BRASIL, **DESTINOS_MUNDO}
 
# Gramado não tem aeroporto — mais próximo é POA ou CXJ
GRAMADO_NOTE = "* Gramado/Canela: voe para Porto Alegre (POA) e pegue ônibus (~3h)"
 
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
        "destinos":     ["DUB", "LIS", "MIA", "EZE"],
        "favorito":     "DUB",
        "preco_max":    5000,
        "data_ida":     "",
        "data_volta":   "",
        "duracao":      14,
        "classe":       "Economy",
        "adultos":      1,
        "pausado":      False,
        "ultimo_preco": {},
        "estado":       None,   # controla fluxo de botões
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
#  TELEGRAM — ENVIO
# ============================================================
 
def send(chat_id, texto, teclado=None, editar_msg_id=None):
    """Envia ou edita mensagem com teclado inline opcional."""
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
        print(f"❌ Telegram {chat_id}: {r.text[:200]}")
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
#  TECLADOS (MENUS)
# ============================================================
 
def teclado_menu_principal(usuario):
    origem_nome = ORIGENS_BRASIL.get(usuario["origem"], usuario["origem"])
    destinos_str = f"{len(usuario['destinos'])} destino(s)"
    data_ida = usuario.get("data_ida") or "Não definida"
    data_volta = usuario.get("data_volta") or "Não definida"
    preco = f"R$ {usuario['preco_max']:,}"
    status = "⏸ Pausado" if usuario.get("pausado") else "▶️ Ativo"
 
    texto = (
        f"✈️ <b>Monitor de Passagens PRO</b>\n\n"
        f"👤 Olá, <b>{usuario.get('nome') or 'Viajante'}</b>!\n\n"
        f"⚙️ <b>Suas configurações:</b>\n"
        f"🛫 Origem: <b>{origem_nome}</b>\n"
        f"🌍 Destinos: <b>{destinos_str}</b>\n"
        f"📅 Ida: <b>{data_ida}</b>\n"
        f"📅 Volta: <b>{data_volta}</b>\n"
        f"💰 Preço máx: <b>{preco}</b>\n"
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
            {"text": "💰 Mudar Preço Máx",       "callback_data": "menu_preco"},
            {"text": "💺 Classe do Voo",         "callback_data": "menu_classe"},
        ],
        [
            {"text": "👥 Nº de Passageiros",     "callback_data": "menu_adultos"},
            {"text": "⭐ Destino Favorito",       "callback_data": "menu_favorito"},
        ],
        [
            {"text": "⏸ Pausar Alertas" if not usuario.get("pausado") else "▶️ Retomar Alertas",
             "callback_data": "toggle_pausa"},
            {"text": "📊 Histórico Semanal",     "callback_data": "resumo"},
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
    botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_principal"}])
    return "🛫 <b>Selecione sua cidade de origem:</b>", botoes
 
 
def teclado_destinos_menu(usuario):
    botoes = [
        [
            {"text": "🇧🇷 Adicionar Brasil",     "callback_data": "add_dest_brasil"},
            {"text": "🌍 Adicionar Internacional","callback_data": "add_dest_mundo"},
        ],
        [{"text": "❌ Remover Destino",          "callback_data": "rem_dest_menu"}],
        [{"text": "🔙 Voltar",                   "callback_data": "menu_principal"}],
    ]
    ativos = "\n".join([f"  • {TODOS_DESTINOS.get(d, d)}" for d in usuario["destinos"]]) or "  Nenhum"
    texto = f"🌍 <b>Seus destinos ativos:</b>\n{ativos}\n\nO que deseja fazer?"
    return texto, botoes
 
 
def teclado_lista_destinos(categoria, usuario, pagina=0):
    if categoria == "brasil":
        fonte = DESTINOS_BRASIL
        titulo = "🇧🇷 <b>Destinos no Brasil:</b>\n(✅ = já ativo)"
    else:
        fonte = DESTINOS_MUNDO
        titulo = "🌍 <b>Destinos Internacionais:</b>\n(✅ = já ativo)"
 
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
            linha.append({"text": f"{marca}{nome}", "callback_data": f"toggle_dest_{cod}"})
        botoes.append(linha)
 
    nav = []
    if pagina > 0:
        nav.append({"text": "◀️ Anterior", "callback_data": f"dest_pag_{categoria}_{pagina-1}"})
    if fim < len(items):
        nav.append({"text": "Próxima ▶️", "callback_data": f"dest_pag_{categoria}_{pagina+1}"})
    if nav:
        botoes.append(nav)
 
    botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_destinos"}])
    return titulo, botoes
 
 
def teclado_datas(usuario):
    hoje = datetime.today()
    opcoes_ida = []
    for semanas in [4, 6, 8, 10, 12, 16, 20, 24]:
        data = hoje + timedelta(weeks=semanas)
        label = data.strftime("%d/%m/%Y")
        valor = data.strftime("%Y-%m-%d")
        opcoes_ida.append((label, valor))
 
    botoes = []
    for i in range(0, len(opcoes_ida), 3):
        linha = []
        for label, valor in opcoes_ida[i:i+3]:
            linha.append({"text": label, "callback_data": f"set_ida_{valor}"})
        botoes.append(linha)
 
    botoes.append([{"text": "📝 Digitar data manualmente", "callback_data": "digitar_data_ida"}])
    botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_principal"}])
 
    data_atual = usuario.get("data_ida") or "não definida"
    texto = (
        f"📅 <b>Selecione a data de ida:</b>\n"
        f"Data atual: <b>{data_atual}</b>\n\n"
        f"Escolha uma das opções ou digite manualmente:"
    )
    return texto, botoes
 
 
def teclado_volta(data_ida):
    ida = datetime.strptime(data_ida, "%Y-%m-%d")
    opcoes = []
    for dias in [7, 10, 14, 21, 30]:
        data = ida + timedelta(days=dias)
        label = f"{dias} dias ({data.strftime('%d/%m/%Y')})"
        valor = data.strftime("%Y-%m-%d")
        opcoes.append((label, valor))
 
    botoes = []
    for label, valor in opcoes:
        botoes.append([{"text": label, "callback_data": f"set_volta_{valor}"}])
    botoes.append([{"text": "📝 Digitar data manualmente", "callback_data": "digitar_data_volta"}])
    botoes.append([{"text": "🚫 Só ida (sem volta)", "callback_data": "set_volta_none"}])
    botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_datas"}])
 
    texto = f"📅 <b>Data de ida:</b> {ida.strftime('%d/%m/%Y')}\n\n<b>Selecione a duração da viagem:</b>"
    return texto, botoes
 
 
def teclado_preco():
    opcoes = [
        ("R$ 1.000",  1000), ("R$ 2.000",  2000),
        ("R$ 3.000",  3000), ("R$ 4.000",  4000),
        ("R$ 5.000",  5000), ("R$ 7.000",  7000),
        ("R$ 10.000", 10000),("R$ 15.000", 15000),
        ("R$ 20.000", 20000),("R$ 30.000", 30000),
    ]
    botoes = []
    for i in range(0, len(opcoes), 3):
        linha = []
        for label, val in opcoes[i:i+3]:
            linha.append({"text": label, "callback_data": f"set_preco_{val}"})
        botoes.append(linha)
    botoes.append([{"text": "📝 Digitar valor", "callback_data": "digitar_preco"}])
    botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_principal"}])
    return "💰 <b>Selecione seu preço máximo por pessoa (ida e volta):</b>", botoes
 
 
def teclado_classe():
    botoes = [
        [
            {"text": "💺 Econômica",        "callback_data": "set_classe_Economy"},
            {"text": "🥈 Econômica Premium","callback_data": "set_classe_Premium_Economy"},
        ],
        [
            {"text": "🥇 Executiva",        "callback_data": "set_classe_Business"},
            {"text": "👑 Primeira Classe",  "callback_data": "set_classe_First"},
        ],
        [{"text": "🔙 Voltar",              "callback_data": "menu_principal"}],
    ]
    return "💺 <b>Selecione a classe do voo:</b>", botoes
 
 
def teclado_adultos():
    botoes = [
        [
            {"text": "👤 1 adulto",  "callback_data": "set_adultos_1"},
            {"text": "👥 2 adultos", "callback_data": "set_adultos_2"},
            {"text": "👨‍👩‍👧 3 adultos", "callback_data": "set_adultos_3"},
        ],
        [
            {"text": "👨‍👩‍👧‍👦 4 adultos","callback_data": "set_adultos_4"},
            {"text": "🏢 5 adultos", "callback_data": "set_adultos_5"},
            {"text": "🏢 6 adultos", "callback_data": "set_adultos_6"},
        ],
        [{"text": "🔙 Voltar",      "callback_data": "menu_principal"}],
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
    botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_principal"}])
    return "⭐ <b>Selecione seu destino favorito (aparece em destaque):</b>", botoes
 
 
# ============================================================
#  FLIGHTAPI — BUSCA REAL
# ============================================================
 
def buscar_voo(origem, destino, data_ida, data_volta, adultos, classe, moeda="BRL"):
    """Busca ida e volta na FlightAPI.io"""
    try:
        if data_volta:
            url = (
                f"https://api.flightapi.io/roundtrip/{FLIGHTAPI_KEY}"
                f"/{origem}/{destino}/{data_ida}/{data_volta}"
                f"/{adultos}/0/0/{classe}/{moeda}"
            )
        else:
            url = (
                f"https://api.flightapi.io/onewaytrip/{FLIGHTAPI_KEY}"
                f"/{origem}/{destino}/{data_ida}"
                f"/{adultos}/0/0/{classe}/{moeda}"
            )
 
        print(f"  🔍 {origem}→{destino} {data_ida}")
        r = requests.get(url, timeout=30)
 
        if r.status_code == 410:
            print(f"  ⚠️ Sem voos para {destino} nessa data")
            return None
        if r.status_code != 200:
            print(f"  ❌ HTTP {r.status_code} para {destino}")
            return None
 
        dados = r.json()
        itinerarios = dados.get("itineraries", [])
        if not itinerarios:
            return None
 
        # Pega o mais barato
        melhor = None
        menor_preco = float("inf")
 
        for itin in itinerarios[:10]:
            pricing = itin.get("pricingOptions", [])
            if not pricing:
                continue
            preco = pricing[0].get("price", {}).get("amount", 0)
            if preco and float(preco) < menor_preco:
                menor_preco = float(preco)
                link = pricing[0].get("deepLink", "")
                legs = dados.get("legs", [])
 
                ida_info = {}
                volta_info = {}
                if legs:
                    leg_ids = itin.get("legIds", [])
                    for leg in legs:
                        if leg.get("id") == (leg_ids[0] if leg_ids else ""):
                            ida_info = leg
                        elif len(leg_ids) > 1 and leg.get("id") == leg_ids[1]:
                            volta_info = leg
 
                melhor = {
                    "origem":    origem,
                    "destino":   destino,
                    "preco":     menor_preco,
                    "moeda":     moeda,
                    "data_ida":  data_ida,
                    "data_volta": data_volta or "—",
                    "duracao_ida": ida_info.get("duration", "—"),
                    "paradas_ida": ida_info.get("stopoversCount", 0),
                    "link":      link,
                    "classe":    classe,
                    "adultos":   adultos,
                }
 
        return melhor
 
    except Exception as e:
        print(f"  ⚠️ Erro buscando {destino}: {e}")
        return None
 
 
def fmt_resultado(oferta):
    destino_nome = TODOS_DESTINOS.get(oferta["destino"], oferta["destino"])
    origem_nome  = ORIGENS_BRASIL.get(oferta["origem"], oferta["origem"])
    paradas = "Direto ✈️" if oferta["paradas_ida"] == 0 else f"{oferta['paradas_ida']} parada(s)"
 
    msg = (
        f"{'🌟 ' if oferta.get('favorito') else ''}"
        f"{destino_nome}\n"
        f"   💵 <b>R$ {oferta['preco']:,.0f}</b> por pessoa\n"
        f"   🛫 {origem_nome}\n"
        f"   📅 Ida: {oferta['data_ida']}"
    )
    if oferta["data_volta"] != "—":
        msg += f" | Volta: {oferta['data_volta']}"
    msg += f"\n   ✈️ {paradas} | 💺 {oferta['classe']}\n"
    if oferta.get("link"):
        msg += f"   🔗 <a href='{oferta['link']}'>Reservar agora</a>\n"
    return msg
 
 
# ============================================================
#  LÓGICA DE BUSCA PARA USUÁRIO
# ============================================================
 
def buscar_para_usuario(usuario):
    if not usuario.get("data_ida"):
        return None, "❌ Defina uma data de ida primeiro! Use o menu abaixo."
 
    origem   = usuario.get("origem", "GRU")
    data_ida = usuario["data_ida"]
    data_volta = usuario.get("data_volta") or ""
    adultos  = usuario.get("adultos", 1)
    classe   = usuario.get("classe", "Economy")
    preco_max = usuario.get("preco_max", 5000)
    favorito = usuario.get("favorito")
 
    ofertas  = []
    quedas   = []
 
    for destino in usuario.get("destinos", []):
        if destino == "GRV":
            destino_real = "POA"  # Gramado → Porto Alegre
        else:
            destino_real = destino
 
        oferta = buscar_voo(origem, destino_real, data_ida, data_volta, adultos, classe)
        if not oferta:
            continue
 
        oferta["destino_original"] = destino
        if destino == "GRV":
            oferta["destino"] = "GRV"
 
        if oferta["preco"] <= preco_max:
            if destino == favorito:
                oferta["favorito"] = True
            ofertas.append(oferta)
 
            anterior = usuario.get("ultimo_preco", {}).get(destino)
            if anterior and anterior > 0:
                queda = (anterior - oferta["preco"]) / anterior * 100
                if queda >= QUEDA_PERC:
                    quedas.append({"oferta": oferta, "anterior": anterior, "perc": queda})
 
        time.sleep(1)  # respeita rate limit
 
    # Atualiza histórico de preços
    with data_lock:
        usuario["ultimo_preco"] = {o["destino_original"]: o["preco"] for o in ofertas}
        salvar()
 
    return ofertas, quedas
 
 
def montar_msg_resultados(usuario, ofertas, quedas):
    if not ofertas:
        return (
            f"😔 <b>Nenhuma oferta encontrada</b>\n\n"
            f"Não encontrei passagens abaixo de R$ {usuario['preco_max']:,} "
            f"para as datas selecionadas.\n\n"
            f"💡 Dicas:\n"
            f"• Tente aumentar o preço máximo\n"
            f"• Mude as datas de viagem\n"
            f"• Adicione mais destinos\n"
        )
 
    ofertas.sort(key=lambda x: x["preco"])
    fav = next((o for o in ofertas if o.get("favorito")), None)
    outras = [o for o in ofertas if not o.get("favorito")]
 
    msg = (
        f"✈️ <b>RESULTADOS DA BUSCA</b>\n"
        f"🗓 {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
        f"💰 Abaixo de R$ {usuario['preco_max']:,} | {len(ofertas)} oferta(s)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
 
    if quedas:
        msg += "🔥 <b>QUEDA DE PREÇO!</b>\n"
        for q in quedas:
            nome = TODOS_DESTINOS.get(q["oferta"]["destino"], q["oferta"]["destino"])
            msg += f"📉 {nome}: R$ {q['anterior']:,.0f} → <b>R$ {q['oferta']['preco']:,.0f}</b> (-{q['perc']:.0f}%)\n"
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
 
    if fav:
        msg += "⭐ <b>SEU FAVORITO</b>\n"
        msg += fmt_resultado(fav) + "\n"
        if fav.get("destino") == "GRV":
            msg += f"   💡 {GRAMADO_NOTE}\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
 
    if outras:
        msg += f"🌍 <b>OUTRAS OFERTAS ({len(outras)})</b>\n\n"
        for o in outras[:8]:
            msg += fmt_resultado(o) + "\n"
            if o.get("destino") == "GRV":
                msg += f"   💡 {GRAMADO_NOTE}\n"
        if len(outras) > 8:
            msg += f"<i>+{len(outras)-8} outras ofertas encontradas.</i>\n"
 
    msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Monitor Passagens PRO"
    return msg
 
 
# ============================================================
#  PROCESSAMENTO DE CALLBACKS (BOTÕES)
# ============================================================
 
def processar_callback(update):
    cb   = update.get("callback_query", {})
    if not cb:
        return
    chat_id     = cb.get("message", {}).get("chat", {}).get("id")
    msg_id      = cb.get("message", {}).get("message_id")
    cb_id       = cb.get("id")
    data        = cb.get("data", "")
    nome        = cb.get("from", {}).get("first_name", "")
 
    if not chat_id:
        return
 
    answer_callback(cb_id)
    usuario = get_user(chat_id, nome)
 
    # ── MENU PRINCIPAL ──────────────────────────────────────
    if data == "menu_principal":
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── ORIGEM ──────────────────────────────────────────────
    elif data == "menu_origem":
        texto, botoes = teclado_origens()
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("set_origem_"):
        cod = data.replace("set_origem_", "")
        usuario["origem"] = cod
        salvar()
        nome_origem = ORIGENS_BRASIL.get(cod, cod)
        answer_callback(cb_id, f"✅ Origem: {nome_origem}")
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── DESTINOS ────────────────────────────────────────────
    elif data == "menu_destinos":
        texto, botoes = teclado_destinos_menu(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data == "add_dest_brasil":
        texto, botoes = teclado_lista_destinos("brasil", usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data == "add_dest_mundo":
        texto, botoes = teclado_lista_destinos("mundo", usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("dest_pag_"):
        partes = data.split("_")
        categoria = partes[2]
        pagina = int(partes[3])
        texto, botoes = teclado_lista_destinos(categoria, usuario, pagina)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("toggle_dest_"):
        cod = data.replace("toggle_dest_", "")
        if cod in usuario["destinos"]:
            usuario["destinos"].remove(cod)
            answer_callback(cb_id, f"❌ {TODOS_DESTINOS.get(cod, cod)} removido")
        else:
            usuario["destinos"].append(cod)
            answer_callback(cb_id, f"✅ {TODOS_DESTINOS.get(cod, cod)} adicionado")
        salvar()
        # Atualiza a lista
        if cod in DESTINOS_BRASIL:
            texto, botoes = teclado_lista_destinos("brasil", usuario)
        else:
            texto, botoes = teclado_lista_destinos("mundo", usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data == "rem_dest_menu":
        botoes = []
        for cod in usuario["destinos"]:
            nome_dest = TODOS_DESTINOS.get(cod, cod)
            botoes.append([{"text": f"❌ {nome_dest}", "callback_data": f"toggle_dest_{cod}"}])
        botoes.append([{"text": "🔙 Voltar", "callback_data": "menu_destinos"}])
        send(chat_id, "❌ <b>Toque para remover um destino:</b>", botoes, editar_msg_id=msg_id)
 
    # ── DATAS ───────────────────────────────────────────────
    elif data == "menu_datas":
        texto, botoes = teclado_datas(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("set_ida_"):
        data_ida = data.replace("set_ida_", "")
        usuario["data_ida"] = data_ida
        usuario["data_volta"] = ""
        salvar()
        texto, botoes = teclado_volta(data_ida)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data == "digitar_data_ida":
        usuario["estado"] = "aguardando_data_ida"
        salvar()
        send(chat_id,
             "📅 <b>Digite a data de ida no formato DD/MM/AAAA:</b>\n"
             "Exemplo: <code>15/07/2026</code>")
 
    elif data == "digitar_data_volta":
        usuario["estado"] = "aguardando_data_volta"
        salvar()
        send(chat_id,
             "📅 <b>Digite a data de volta no formato DD/MM/AAAA:</b>\n"
             "Exemplo: <code>29/07/2026</code>")
 
    elif data.startswith("set_volta_"):
        val = data.replace("set_volta_", "")
        usuario["data_volta"] = "" if val == "none" else val
        salvar()
        answer_callback(cb_id, "✅ Datas configuradas!")
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── PREÇO ───────────────────────────────────────────────
    elif data == "menu_preco":
        texto, botoes = teclado_preco()
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("set_preco_"):
        val = int(data.replace("set_preco_", ""))
        usuario["preco_max"] = val
        salvar()
        answer_callback(cb_id, f"✅ Preço máx: R$ {val:,}")
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data == "digitar_preco":
        usuario["estado"] = "aguardando_preco"
        salvar()
        send(chat_id, "💰 <b>Digite o preço máximo em reais:</b>\nExemplo: <code>4500</code>")
 
    # ── CLASSE ──────────────────────────────────────────────
    elif data == "menu_classe":
        texto, botoes = teclado_classe()
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("set_classe_"):
        classe = data.replace("set_classe_", "")
        usuario["classe"] = classe
        salvar()
        nomes = {"Economy":"Econômica","Premium_Economy":"Econômica Premium",
                 "Business":"Executiva","First":"Primeira Classe"}
        answer_callback(cb_id, f"✅ Classe: {nomes.get(classe, classe)}")
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── ADULTOS ─────────────────────────────────────────────
    elif data == "menu_adultos":
        texto, botoes = teclado_adultos()
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("set_adultos_"):
        n = int(data.replace("set_adultos_", ""))
        usuario["adultos"] = n
        salvar()
        answer_callback(cb_id, f"✅ {n} adulto(s)")
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── FAVORITO ────────────────────────────────────────────
    elif data == "menu_favorito":
        texto, botoes = teclado_favorito(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    elif data.startswith("set_fav_"):
        cod = data.replace("set_fav_", "")
        usuario["favorito"] = cod
        salvar()
        nome_fav = TODOS_DESTINOS.get(cod, cod)
        answer_callback(cb_id, f"⭐ Favorito: {nome_fav}")
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── PAUSAR/RETOMAR ──────────────────────────────────────
    elif data == "toggle_pausa":
        usuario["pausado"] = not usuario.get("pausado", False)
        salvar()
        status = "⏸ Alertas pausados" if usuario["pausado"] else "▶️ Alertas retomados"
        answer_callback(cb_id, status)
        texto, botoes = teclado_menu_principal(usuario)
        send(chat_id, texto, botoes, editar_msg_id=msg_id)
 
    # ── BUSCAR AGORA ────────────────────────────────────────
    elif data == "buscar":
        if not usuario.get("data_ida"):
            send(chat_id,
                 "⚠️ <b>Defina uma data de ida primeiro!</b>",
                 [[{"text": "📅 Definir Data", "callback_data": "menu_datas"}]])
            return
        send(chat_id, "🔍 <b>Buscando as melhores passagens...</b>\nIsso pode levar alguns segundos. ✈️")
        threading.Thread(target=_buscar_e_responder, args=(usuario,), daemon=True).start()
 
    # ── RESUMO SEMANAL ──────────────────────────────────────
    elif data == "resumo":
        enviar_resumo_usuario(usuario)
 
 
def _buscar_e_responder(usuario):
    ofertas, quedas = buscar_para_usuario(usuario)
    if ofertas is None:
        send(usuario["chat_id"], quedas)  # quedas aqui é a mensagem de erro
        return
    msg = montar_msg_resultados(usuario, ofertas, quedas)
    botoes = [[{"text": "🔙 Voltar ao Menu", "callback_data": "menu_principal"}]]
    send(usuario["chat_id"], msg, botoes)
 
 
# ============================================================
#  PROCESSAMENTO DE MENSAGENS DE TEXTO
# ============================================================
 
def processar_mensagem(update):
    msg = update.get("message", {})
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
 
    # ── COMANDOS ────────────────────────────────────────────
    if texto.startswith("/start") or texto.startswith("/menu"):
        usuario["nome"] = nome
        usuario["estado"] = None
        salvar()
        txt, botoes = teclado_menu_principal(usuario)
        send(chat_id, txt, botoes)
        return
 
    if texto.startswith("/ajuda"):
        send(chat_id,
             "✈️ <b>Como usar o Monitor de Passagens PRO:</b>\n\n"
             "1️⃣ Digite /start para abrir o menu\n"
             "2️⃣ Configure sua <b>origem</b> (de onde vai sair)\n"
             "3️⃣ Adicione seus <b>destinos</b> favoritos\n"
             "4️⃣ Defina as <b>datas</b> da viagem\n"
             "5️⃣ Configure o <b>preço máximo</b>\n"
             "6️⃣ Clique em <b>Buscar Agora</b>!\n\n"
             "O bot também busca automaticamente a cada "
             f"{VERIFICAR_HORAS}h e te avisa se encontrar promoções! 🔔")
        return
 
    # ── ESTADOS (aguardando input do usuário) ────────────────
    if estado == "aguardando_data_ida":
        try:
            dt = datetime.strptime(texto.strip(), "%d/%m/%Y")
            if dt.date() <= datetime.today().date():
                send(chat_id, "⚠️ A data precisa ser no futuro! Tente novamente:")
                return
            usuario["data_ida"] = dt.strftime("%Y-%m-%d")
            usuario["data_volta"] = ""
            usuario["estado"] = None
            salvar()
            texto_teclado, botoes = teclado_volta(usuario["data_ida"])
            send(chat_id, texto_teclado, botoes)
        except ValueError:
            send(chat_id, "⚠️ Formato inválido! Use DD/MM/AAAA\nExemplo: <code>15/07/2026</code>")
        return
 
    if estado == "aguardando_data_volta":
        try:
            dt = datetime.strptime(texto.strip(), "%d/%m/%Y")
            ida = datetime.strptime(usuario["data_ida"], "%Y-%m-%d")
            if dt.date() <= ida.date():
                send(chat_id, "⚠️ A data de volta precisa ser depois da ida! Tente novamente:")
                return
            usuario["data_volta"] = dt.strftime("%Y-%m-%d")
            usuario["estado"] = None
            salvar()
            txt, botoes = teclado_menu_principal(usuario)
            send(chat_id, f"✅ Datas configuradas!\n\n" + txt, botoes)
        except ValueError:
            send(chat_id, "⚠️ Formato inválido! Use DD/MM/AAAA\nExemplo: <code>29/07/2026</code>")
        return
 
    if estado == "aguardando_preco":
        try:
            val = int(texto.strip().replace(".", "").replace(",", "").replace("R$","").strip())
            if val < 100:
                send(chat_id, "⚠️ Valor muito baixo! Tente um valor maior:")
                return
            usuario["preco_max"] = val
            usuario["estado"] = None
            salvar()
            txt, botoes = teclado_menu_principal(usuario)
            send(chat_id, f"✅ Preço máximo: R$ {val:,}\n\n" + txt, botoes)
        except ValueError:
            send(chat_id, "⚠️ Digite apenas números. Exemplo: <code>4500</code>")
        return
 
    # ── MENSAGEM NÃO RECONHECIDA ─────────────────────────────
    txt, botoes = teclado_menu_principal(usuario)
    send(chat_id, txt, botoes)
 
 
# ============================================================
#  VERIFICAÇÃO AUTOMÁTICA
# ============================================================
 
def verificar_automatico():
    print(f"\n[{datetime.now()}] 🔍 Verificação automática...")
    with data_lock:
        usuarios = [deepcopy(u) for u in state["users"].values()
                    if not u.get("pausado") and u.get("data_ida")]
 
    if not usuarios:
        print(f"[{datetime.now()}] Nenhum usuário com data definida.")
        return
 
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
                botoes = [[{"text": "⚙️ Configurações", "callback_data": "menu_principal"}]]
                send(vivo["chat_id"], msg, botoes)
            else:
                send(vivo["chat_id"],
                     f"🔍 Verificação automática: nenhuma oferta abaixo de "
                     f"R$ {vivo['preco_max']:,} para as datas configuradas.")
        except Exception as e:
            print(f"⚠️ Erro em {usuario['chat_id']}: {e}")
 
    print(f"[{datetime.now()}] ✅ Verificação automática concluída.")
 
 
def enviar_resumo_usuario(usuario):
    with data_lock:
        historico = [e for e in state.get("historico_semana", [])
                     if e.get("chat_id") == usuario["chat_id"]]
 
    if not historico:
        send(usuario["chat_id"],
             "📅 <b>Resumo Semanal</b>\n\nNenhuma busca realizada esta semana.\n"
             "Use o menu para configurar e buscar passagens!",
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
        f"💎 Top {len(ranking)} ofertas da semana\n"
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
                    print(f"⚠️ Erro update: {e}")
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            print(f"⚠️ Polling: {e}")
            time.sleep(5)
 
 
def scheduler_loop():
    schedule.every(VERIFICAR_HORAS).hours.do(verificar_automatico)
    schedule.every().sunday.at("09:00").do(resumo_semanal_todos)
    print(f"[{datetime.now()}] ⏰ Agendador: a cada {VERIFICAR_HORAS}h + resumo dom 09:00")
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
    print("✈️  Monitor de Passagens PRO — Com Botões Interativos")
    print(f"    {len(TODOS_DESTINOS)} destinos | FlightAPI.io")
    print("=" * 60)
 
    carregar()
 
    send(ADMIN_CHAT_ID,
         "🚀 <b>Monitor PRO v2 online!</b>\n\n"
         f"✨ Agora com botões interativos!\n"
         f"🌍 {len(TODOS_DESTINOS)} destinos disponíveis\n"
         f"🇧🇷 Incluindo cidades brasileiras\n"
         f"📅 Configure datas pelo menu\n"
         f"⏰ Verificação a cada {VERIFICAR_HORAS}h\n\n"
         "Use /start para abrir o menu! ✈️")
 
    threading.Thread(target=scheduler_loop, daemon=True).start()
    polling()
 
 
if __name__ == "__main__":
    main()
