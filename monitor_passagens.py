"""
✈️  Monitor de Passagens PRO — Telegram + Travelpayouts
Versão com sistema multi-usuário, comandos interativos, alertas de queda
de preço, resumo semanal e persistência em JSON.

Pronto para rodar no Railway. Configure as variáveis de ambiente:
    TELEGRAM_TOKEN     — token do BotFather
    TRAVEL_TOKEN       — token Travelpayouts
    TELEGRAM_CHAT_ID   — (opcional) admin/owner para mensagens de boot
    DATA_FILE          — (opcional) caminho do JSON de persistência
    PRECO_MAXIMO_PADRAO— (opcional) limite default em R$ (default 20000)
    VERIFICAR_HORAS    — (opcional) intervalo de verificação (default 6)
"""

import os
import json
import time
import threading
from datetime import datetime
from copy import deepcopy

import requests
import schedule

# ============================================================
#  CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TRAVEL_TOKEN     = os.getenv("TRAVEL_TOKEN", "")
ADMIN_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")  # opcional

ORIGEM             = os.getenv("ORIGEM", "GRU")
PRECO_MAXIMO_PAD   = int(os.getenv("PRECO_MAXIMO_PADRAO", "20000"))
VERIFICAR_HORAS    = int(os.getenv("VERIFICAR_HORAS", "6"))
DATA_FILE          = os.getenv("DATA_FILE", "users.json")
QUEDA_PERCENTUAL   = 15  # % para disparar alerta de queda

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ============================================================
#  DESTINOS DISPONÍVEIS
# ============================================================
DESTINOS = [
    # ⭐ FOCO PRINCIPAL
    ("DUB", "Dublin, Irlanda 🌟 (gateway Estônia)", "🇮🇪"),

    # 🔵 HUBS EUROPEUS COM CONEXÃO PARA TALLINN
    ("FRA", "Frankfurt, Alemanha (hub → Tallinn)",  "🇩🇪"),
    ("IST", "Istambul, Turquia (hub → Tallinn)",    "🇹🇷"),
    ("ARN", "Estocolmo, Suécia (hub → Tallinn)",    "🇸🇪"),
    ("HEL", "Helsinki, Finlândia (hub → Tallinn)",  "🇫🇮"),
    ("RIX", "Riga, Letônia (hub → Tallinn)",        "🇱🇻"),
    ("WAW", "Varsóvia, Polônia (hub → Tallinn)",    "🇵🇱"),

    # 🌍 EUROPA
    ("CDG", "Paris, França",                        "🇫🇷"),
    ("LHR", "Londres, Reino Unido",                 "🇬🇧"),
    ("MAD", "Madri, Espanha",                       "🇪🇸"),
    ("LIS", "Lisboa, Portugal",                     "🇵🇹"),
    ("FCO", "Roma, Itália",                         "🇮🇹"),
    ("AMS", "Amsterdã, Holanda",                    "🇳🇱"),
    ("VIE", "Viena, Áustria",                       "🇦🇹"),
    ("PRG", "Praga, Rep. Tcheca",                   "🇨🇿"),
    ("BUD", "Budapeste, Hungria",                   "🇭🇺"),
    ("ATH", "Atenas, Grécia",                       "🇬🇷"),
    ("CPH", "Copenhague, Dinamarca",                "🇩🇰"),
    ("OSL", "Oslo, Noruega",                        "🇳🇴"),
    ("OTP", "Bucareste, Romênia",                   "🇷🇴"),
    ("BEG", "Belgrado, Sérvia",                     "🇷🇸"),
    ("VNO", "Vilnius, Lituânia",                    "🇱🇹"),
    ("TBS", "Tbilisi, Geórgia",                     "🇬🇪"),
    ("SVO", "Moscou, Rússia",                       "🇷🇺"),

    # 🌎 AMÉRICAS
    ("EZE", "Buenos Aires, Argentina",              "🇦🇷"),
    ("MEX", "Cidade do México, México",             "🇲🇽"),
    ("IAD", "Washington D.C., EUA",                 "🇺🇸"),
    ("JFK", "Nova York, EUA",                       "🇺🇸"),
    ("LAX", "Los Angeles, EUA",                     "🇺🇸"),
    ("YYZ", "Toronto, Canadá",                      "🇨🇦"),
    ("SCL", "Santiago, Chile",                      "🇨🇱"),
    ("LIM", "Lima, Peru",                           "🇵🇪"),
    ("BOG", "Bogotá, Colômbia",                     "🇨🇴"),
    ("MVD", "Montevidéu, Uruguai",                  "🇺🇾"),
    ("PTY", "Cidade do Panamá, Panamá",             "🇵🇦"),
    ("HAV", "Havana, Cuba",                         "🇨🇺"),

    # 🌏 ÁSIA
    ("NRT", "Tóquio, Japão",                        "🇯🇵"),
    ("PEK", "Pequim, China",                        "🇨🇳"),
    ("ICN", "Seul, Coreia do Sul",                  "🇰🇷"),
    ("DEL", "Nova Delhi, Índia",                    "🇮🇳"),
    ("BKK", "Bangkok, Tailândia",                   "🇹🇭"),
    ("SIN", "Singapura",                            "🇸🇬"),
    ("KUL", "Kuala Lumpur, Malásia",                "🇲🇾"),
    ("CGK", "Jacarta, Indonésia",                   "🇮🇩"),
    ("MNL", "Manila, Filipinas",                    "🇵🇭"),
    ("HAN", "Hanói, Vietnã",                        "🇻🇳"),
    ("DXB", "Dubai, Emirados Árabes",               "🇦🇪"),
    ("TLV", "Tel Aviv, Israel",                     "🇮🇱"),

    # 🌍 ÁFRICA
    ("CAI", "Cairo, Egito",                         "🇪🇬"),
    ("NBO", "Nairóbi, Quênia",                      "🇰🇪"),
    ("JNB", "Joanesburgo, África do Sul",           "🇿🇦"),
    ("LOS", "Lagos, Nigéria",                       "🇳🇬"),
    ("CMN", "Casablanca, Marrocos",                 "🇲🇦"),
    ("ADD", "Adis Abeba, Etiópia",                  "🇪🇹"),
    ("LAD", "Luanda, Angola",                       "🇦🇴"),
    ("MPM", "Maputo, Moçambique",                   "🇲🇿"),

    # 🌏 OCEANIA
    ("SYD", "Sydney, Austrália",                    "🇦🇺"),
    ("AKL", "Auckland, Nova Zelândia",              "🇳🇿"),
]

# Dicionário rápido por código IATA
DESTINOS_MAP = {cod: (cod, nome, emoji) for cod, nome, emoji in DESTINOS}

# Padrão de destinos ativos para novos usuários (foco Estônia)
DESTINOS_PADRAO = ["DUB", "FRA", "IST", "ARN", "HEL", "RIX", "WAW"]

# ============================================================
#  PERSISTÊNCIA
# ============================================================
data_lock = threading.RLock()
state = {
    "users": {},          # chat_id (str) -> dados do usuário
    "ofertas_semana": [], # acumulador para resumo de domingo
}


def carregar_dados():
    global state
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                state.setdefault("users", {})
                state.setdefault("ofertas_semana", [])
            print(f"[{datetime.now()}] 📂 Dados carregados: {len(state['users'])} usuário(s).")
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ Erro ao carregar {DATA_FILE}: {e}")


def salvar_dados():
    with data_lock:
        try:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DATA_FILE)
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ Erro ao salvar {DATA_FILE}: {e}")


def novo_usuario(chat_id, nome=""):
    return {
        "chat_id":      str(chat_id),
        "nome":         nome,
        "preco_max":    PRECO_MAXIMO_PAD,
        "destinos":     list(DESTINOS_PADRAO),
        "favorito":     "DUB",
        "meses":        [],   # vazio = qualquer mês
        "pausado":      False,
        "ultimo_preco": {},   # {IATA: ultimo_preco_visto}
        "criado_em":    datetime.now().isoformat(timespec="seconds"),
    }


def get_user(chat_id, nome=""):
    cid = str(chat_id)
    with data_lock:
        if cid not in state["users"]:
            state["users"][cid] = novo_usuario(cid, nome)
            salvar_dados()
        return state["users"][cid]


# ============================================================
#  TELEGRAM
# ============================================================

def enviar_telegram(chat_id, mensagem, disable_preview=True):
    if not TELEGRAM_TOKEN:
        print(f"[{datetime.now()}] ⚠️ TELEGRAM_TOKEN não configurado.")
        return False
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id":                  str(chat_id),
        "text":                     mensagem,
        "parse_mode":               "HTML",
        "disable_web_page_preview": disable_preview,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return True
        print(f"[{datetime.now()}] ❌ Erro Telegram {chat_id}: {r.text}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Conexão Telegram {chat_id}: {e}")
    return False


def broadcast(mensagem, somente_ativos=True):
    """Envia mensagem para todos os usuários (ou só os ativos)."""
    with data_lock:
        usuarios = list(state["users"].values())
    for u in usuarios:
        if somente_ativos and u.get("pausado"):
            continue
        enviar_telegram(u["chat_id"], mensagem)
        time.sleep(0.3)


# ============================================================
#  BUSCA DE OFERTAS
# ============================================================

def montar_link_kayak(origem, destino, data_ida, data_volta):
    ida   = data_ida   if data_ida   and data_ida   != "—" else ""
    volta = data_volta if data_volta and data_volta != "—" else ""
    if ida and volta:
        return f"https://www.kayak.com.br/flights/{origem}-{destino}/{ida}/{volta}"
    if ida:
        return f"https://www.kayak.com.br/flights/{origem}-{destino}/{ida}"
    return f"https://www.kayak.com.br/flights/{origem}-{destino}"


def buscar_ofertas_destino(codigo_iata):
    """Retorna lista de ofertas para um destino, ordenadas por preço."""
    if not TRAVEL_TOKEN:
        return []
    try:
        url = "https://api.travelpayouts.com/v2/prices/month-matrix"
        params = {
            "origin":             ORIGEM,
            "destination":        codigo_iata,
            "currency":           "brl",
            "show_to_affiliates": "true",
            "token":              TRAVEL_TOKEN,
        }
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            print(f"  [{codigo_iata}] HTTP {r.status_code}")
            return []
        lista = r.json().get("data") or []
        ofertas = []
        for item in lista:
            preco = item.get("value")
            if preco is None:
                continue
            data_ida   = item.get("depart_date") or ""
            data_volta = item.get("return_date") or ""
            ofertas.append({
                "iata":       codigo_iata,
                "preco":      float(preco),
                "data_ida":   data_ida or "—",
                "data_volta": data_volta or "—",
                "cia":        item.get("gate") or "—",
                "link":       montar_link_kayak(ORIGEM, codigo_iata, data_ida, data_volta),
            })
        ofertas.sort(key=lambda o: o["preco"])
        return ofertas
    except Exception as e:
        print(f"  ⚠️ Erro buscando {codigo_iata}: {e}")
        return []


def filtrar_por_meses(ofertas, meses):
    """Filtra ofertas mantendo só as do mês de ida em `meses` (1-12)."""
    if not meses:
        return ofertas
    out = []
    for o in ofertas:
        try:
            mes = int(o["data_ida"].split("-")[1])
            if mes in meses:
                out.append(o)
        except Exception:
            continue
    return out


def melhor_oferta_para_usuario(usuario, codigo_iata, cache):
    """Devolve a melhor oferta de um destino respeitando filtros do usuário."""
    if codigo_iata not in cache:
        cache[codigo_iata] = buscar_ofertas_destino(codigo_iata)
        time.sleep(0.4)  # gentil com a API
    ofertas = filtrar_por_meses(cache[codigo_iata], usuario.get("meses") or [])
    ofertas = [o for o in ofertas if o["preco"] <= usuario["preco_max"]]
    return ofertas[0] if ofertas else None


# ============================================================
#  FORMATAÇÃO DE MENSAGEM
# ============================================================

def fmt_oferta(o, prefix=""):
    cod = o["iata"]
    _, nome, emoji = DESTINOS_MAP.get(cod, (cod, cod, "✈️"))
    linha = (
        f"{prefix}{emoji} <b>{nome}</b> — R$ {o['preco']:,.0f}\n"
        f"   📅 {o['data_ida']}"
    )
    if o.get("data_volta") and o["data_volta"] != "—":
        linha += f" → {o['data_volta']}"
    linha += f" | 🏢 {o['cia']}\n"
    linha += f"   🔗 <a href='{o['link']}'>Buscar no Kayak</a>\n"
    return linha


def montar_mensagem_alertas(usuario, ofertas, quedas):
    favorito = usuario.get("favorito")
    fav_oferta = next((o for o in ofertas if o["iata"] == favorito), None)
    hubs   = [o for o in ofertas if "hub" in DESTINOS_MAP.get(o["iata"], (None, "", ""))[1] and o["iata"] != favorito]
    outras = [o for o in ofertas
              if o["iata"] != favorito
              and "hub" not in DESTINOS_MAP.get(o["iata"], (None, "", ""))[1]]

    msg = (
        f"✈️ <b>ALERTAS DE PASSAGENS</b>\n"
        f"🗓 {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
        f"💰 Limite: R$ {usuario['preco_max']:,} | {len(ofertas)} oferta(s)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if quedas:
        msg += "🔥 <b>QUEDA DE PREÇO!</b>\n"
        for q in quedas:
            cod = q["oferta"]["iata"]
            _, nome, emoji = DESTINOS_MAP.get(cod, (cod, cod, "✈️"))
            msg += (
                f"{emoji} <b>{nome}</b>\n"
                f"   📉 R$ {q['anterior']:,.0f} → <b>R$ {q['oferta']['preco']:,.0f}</b> "
                f"(-{q['percentual']:.0f}%)\n"
                f"   🔗 <a href='{q['oferta']['link']}'>Buscar no Kayak</a>\n"
            )
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"

    if fav_oferta:
        _, nome, emoji = DESTINOS_MAP.get(favorito, (favorito, favorito, "⭐"))
        msg += (
            f"⭐ <b>SEU FAVORITO</b>\n"
            f"{emoji} <b>{nome}</b>\n"
            f"   💵 <b>R$ {fav_oferta['preco']:,.0f}</b>\n"
            f"   📅 Ida: {fav_oferta['data_ida']}"
        )
        if fav_oferta["data_volta"] != "—":
            msg += f" → Volta: {fav_oferta['data_volta']}"
        msg += (
            f"\n   🏢 {fav_oferta['cia']}\n"
            f"   🔗 <a href='{fav_oferta['link']}'>Buscar no Kayak</a>\n"
            f"\n━━━━━━━━━━━━━━━━━━━━\n\n"
        )

    if hubs:
        msg += "🔵 <b>HUBS COM VOO PARA TALLINN</b>\n\n"
        for o in hubs:
            msg += fmt_oferta(o) + "\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    if outras:
        msg += "🌍 <b>OUTRAS OFERTAS</b>\n\n"
        for o in outras[:10]:
            msg += fmt_oferta(o) + "\n"
        if len(outras) > 10:
            msg += f"<i>+{len(outras)-10} outras ofertas encontradas.</i>\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Monitor automático de passagens"
    return msg


# ============================================================
#  VERIFICAÇÃO PRINCIPAL
# ============================================================

def verificar_para_usuario(usuario, cache):
    if usuario.get("pausado"):
        return None

    ofertas = []
    quedas  = []
    novos_precos = {}

    for cod in usuario["destinos"]:
        if cod not in DESTINOS_MAP:
            continue
        oferta = melhor_oferta_para_usuario(usuario, cod, cache)
        if not oferta:
            continue
        ofertas.append(oferta)
        novos_precos[cod] = oferta["preco"]

        anterior = usuario.get("ultimo_preco", {}).get(cod)
        if anterior and anterior > 0:
            queda = (anterior - oferta["preco"]) / anterior * 100
            if queda >= QUEDA_PERCENTUAL:
                quedas.append({
                    "oferta":     oferta,
                    "anterior":   anterior,
                    "percentual": queda,
                })

    # Atualiza histórico de preços
    with data_lock:
        usuario["ultimo_preco"] = novos_precos
        salvar_dados()

    if not ofertas:
        return None

    ofertas.sort(key=lambda o: o["preco"])
    return {"ofertas": ofertas, "quedas": quedas}


def verificar_todos():
    print(f"\n[{datetime.now()}] 🔍 Iniciando verificação global...")
    with data_lock:
        usuarios = [deepcopy(u) for u in state["users"].values() if not u.get("pausado")]

    if not usuarios:
        print(f"[{datetime.now()}] Nenhum usuário ativo.")
        return

    cache = {}  # IATA -> ofertas brutas (compartilhado entre usuários)

    for usuario in usuarios:
        try:
            print(f"  → Usuário {usuario['chat_id']} ({len(usuario['destinos'])} destinos)")
            # Pega o usuário "vivo" para gravar histórico
            with data_lock:
                vivo = state["users"].get(usuario["chat_id"])
                if not vivo:
                    continue
            resultado = verificar_para_usuario(vivo, cache)
            if not resultado:
                enviar_telegram(
                    usuario["chat_id"],
                    f"🔍 <b>Verificação concluída</b>\n\n"
                    f"Nenhuma passagem abaixo de R$ {usuario['preco_max']:,} no momento.\n"
                    f"Próxima verificação em {VERIFICAR_HORAS}h. ⏰"
                )
                continue

            msg = montar_mensagem_alertas(usuario, resultado["ofertas"], resultado["quedas"])
            enviar_telegram(usuario["chat_id"], msg)

            # Acumula no histórico semanal
            with data_lock:
                state["ofertas_semana"].append({
                    "chat_id": usuario["chat_id"],
                    "ts":      datetime.now().isoformat(timespec="seconds"),
                    "ofertas": resultado["ofertas"][:5],
                })
                # Limita o histórico a algo razoável
                if len(state["ofertas_semana"]) > 5000:
                    state["ofertas_semana"] = state["ofertas_semana"][-5000:]
                salvar_dados()
        except Exception as e:
            print(f"  ⚠️ Erro processando {usuario['chat_id']}: {e}")

    print(f"[{datetime.now()}] ✅ Verificação concluída.")


# ============================================================
#  RESUMO SEMANAL
# ============================================================

def resumo_semanal():
    print(f"[{datetime.now()}] 📅 Gerando resumo semanal...")
    with data_lock:
        historico = list(state.get("ofertas_semana", []))
        usuarios = list(state["users"].values())

    by_user = {}
    for entry in historico:
        by_user.setdefault(entry["chat_id"], []).extend(entry["ofertas"])

    for u in usuarios:
        if u.get("pausado"):
            continue
        ofertas = by_user.get(u["chat_id"], [])
        if not ofertas:
            enviar_telegram(
                u["chat_id"],
                "📅 <b>RESUMO SEMANAL</b>\n\n"
                "Nenhuma oferta foi capturada esta semana dentro do seu limite.\n"
                "Use /preco para ajustar seu teto. ✈️"
            )
            continue

        # Agrupa por destino, fica com o melhor preço
        melhores = {}
        for o in ofertas:
            atual = melhores.get(o["iata"])
            if not atual or o["preco"] < atual["preco"]:
                melhores[o["iata"]] = o
        ranking = sorted(melhores.values(), key=lambda x: x["preco"])[:10]

        msg = (
            f"📅 <b>RESUMO SEMANAL</b>\n"
            f"🗓 {datetime.now().strftime('%d/%m/%Y')}\n"
            f"💎 Top {len(ranking)} ofertas da semana\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for i, o in enumerate(ranking, 1):
            msg += fmt_oferta(o, prefix=f"<b>#{i}</b> ") + "\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Bom domingo! ✈️"
        enviar_telegram(u["chat_id"], msg)

    # Limpa histórico semanal
    with data_lock:
        state["ofertas_semana"] = []
        salvar_dados()
    print(f"[{datetime.now()}] ✅ Resumo semanal enviado.")


# ============================================================
#  COMANDOS DO TELEGRAM
# ============================================================

MENU = (
    "🤖 <b>Menu de comandos</b>\n\n"
    "/start — cadastra você no bot\n"
    "/preco 5000 — define seu preço máximo (R$)\n"
    "/destinos — lista todos os destinos disponíveis\n"
    "/ativar DUB LIS CDG — ativa destinos\n"
    "/desativar DUB — desativa um destino\n"
    "/favorito DUB — define destino favorito\n"
    "/meses 6 7 8 — filtra meses (vazio = todos)\n"
    "/meus — mostra suas configurações\n"
    "/buscar — força uma busca imediata\n"
    "/pausar — pausa alertas\n"
    "/retomar — retoma alertas\n"
    "/ajuda — mostra este menu"
)


def cmd_start(usuario, args):
    usuario["nome"] = usuario.get("nome") or ""
    salvar_dados()
    return (
        f"🚀 <b>Bem-vindo ao Monitor de Passagens PRO!</b>\n\n"
        f"Você foi cadastrado. Suas configurações iniciais:\n"
        f"💰 Preço máximo: R$ {usuario['preco_max']:,}\n"
        f"⭐ Favorito: {usuario['favorito']}\n"
        f"🌍 Destinos ativos: {len(usuario['destinos'])}\n\n"
        f"Use /ajuda para ver todos os comandos.\n"
        f"Use /buscar para uma busca imediata. ✈️"
    )


def cmd_preco(usuario, args):
    if not args:
        return f"💰 Seu preço máximo atual é <b>R$ {usuario['preco_max']:,}</b>.\nUse: /preco 5000"
    try:
        valor = int(args[0].replace(".", "").replace(",", ""))
        if valor < 100:
            return "⚠️ Valor muito baixo. Use algo como /preco 5000"
        usuario["preco_max"] = valor
        salvar_dados()
        return f"✅ Preço máximo atualizado para <b>R$ {valor:,}</b>."
    except ValueError:
        return "⚠️ Formato inválido. Exemplo: /preco 5000"


def cmd_destinos(usuario, args):
    msg = "🌍 <b>Destinos disponíveis</b>\n\n"
    linhas = []
    for cod, nome, emoji in DESTINOS:
        marca = "✅" if cod in usuario["destinos"] else "⬜"
        linhas.append(f"{marca} <code>{cod}</code> {emoji} {nome}")
    # Telegram aceita até ~4096 chars; quebra se necessário
    chunk = []
    tamanho = len(msg)
    for linha in linhas:
        if tamanho + len(linha) + 1 > 3800:
            yield_msg = msg + "\n".join(chunk)
            enviar_telegram(usuario["chat_id"], yield_msg)
            chunk = []
            tamanho = 0
            msg = ""
        chunk.append(linha)
        tamanho += len(linha) + 1
    if chunk:
        return msg + "\n".join(chunk)
    return None


def cmd_ativar(usuario, args):
    if not args:
        return "Use: /ativar DUB LIS CDG"
    adicionados, invalidos = [], []
    for code in args:
        c = code.upper()
        if c not in DESTINOS_MAP:
            invalidos.append(c)
            continue
        if c not in usuario["destinos"]:
            usuario["destinos"].append(c)
            adicionados.append(c)
    salvar_dados()
    out = ""
    if adicionados:
        out += f"✅ Ativados: {', '.join(adicionados)}\n"
    if invalidos:
        out += f"⚠️ Inválidos: {', '.join(invalidos)}\n"
    if not out:
        out = "Nenhuma alteração."
    return out.strip()


def cmd_desativar(usuario, args):
    if not args:
        return "Use: /desativar DUB"
    removidos, ausentes = [], []
    for code in args:
        c = code.upper()
        if c in usuario["destinos"]:
            usuario["destinos"].remove(c)
            removidos.append(c)
        else:
            ausentes.append(c)
    salvar_dados()
    out = ""
    if removidos:
        out += f"❌ Desativados: {', '.join(removidos)}\n"
    if ausentes:
        out += f"⚠️ Não estavam ativos: {', '.join(ausentes)}\n"
    return out.strip() or "Nenhuma alteração."


def cmd_favorito(usuario, args):
    if not args:
        return f"⭐ Seu favorito atual: <b>{usuario.get('favorito') or '—'}</b>\nUse: /favorito DUB"
    c = args[0].upper()
    if c not in DESTINOS_MAP:
        return f"⚠️ Código inválido: {c}"
    usuario["favorito"] = c
    if c not in usuario["destinos"]:
        usuario["destinos"].append(c)
    salvar_dados()
    _, nome, emoji = DESTINOS_MAP[c]
    return f"⭐ Favorito atualizado: {emoji} <b>{nome}</b>"


def cmd_meses(usuario, args):
    if not args:
        atuais = usuario.get("meses") or []
        if not atuais:
            return "📆 Nenhum filtro de mês ativo (todos os meses).\nUse: /meses 6 7 8"
        return f"📆 Meses ativos: {', '.join(map(str, atuais))}\nUse /meses sem números para limpar."
    meses = []
    for a in args:
        try:
            m = int(a)
            if 1 <= m <= 12:
                meses.append(m)
        except ValueError:
            pass
    usuario["meses"] = sorted(set(meses))
    salvar_dados()
    if not usuario["meses"]:
        return "📆 Filtro de meses removido (todos os meses)."
    return f"📆 Filtro atualizado: meses {', '.join(map(str, usuario['meses']))}"


def cmd_meus(usuario, args):
    meses = usuario.get("meses") or []
    meses_txt = ", ".join(map(str, meses)) if meses else "todos"
    favorito = usuario.get("favorito") or "—"
    nome_fav = DESTINOS_MAP.get(favorito, (favorito, favorito, ""))[1]
    return (
        f"⚙️ <b>Suas configurações</b>\n\n"
        f"💰 Preço máximo: R$ {usuario['preco_max']:,}\n"
        f"⭐ Favorito: {favorito} — {nome_fav}\n"
        f"📆 Meses: {meses_txt}\n"
        f"🌍 Destinos ativos ({len(usuario['destinos'])}):\n"
        f"   {', '.join(usuario['destinos']) or '—'}\n"
        f"⏯ Status: {'⏸ Pausado' if usuario.get('pausado') else '▶️ Ativo'}\n"
    )


def cmd_buscar(usuario, args):
    enviar_telegram(usuario["chat_id"], "🔍 Buscando agora… isso pode levar alguns segundos.")
    cache = {}
    resultado = verificar_para_usuario(usuario, cache)
    if not resultado:
        return f"Nenhuma oferta abaixo de R$ {usuario['preco_max']:,} no momento."
    msg = montar_mensagem_alertas(usuario, resultado["ofertas"], resultado["quedas"])
    enviar_telegram(usuario["chat_id"], msg)
    return None


def cmd_pausar(usuario, args):
    usuario["pausado"] = True
    salvar_dados()
    return "⏸ Alertas pausados. Use /retomar para reativar."


def cmd_retomar(usuario, args):
    usuario["pausado"] = False
    salvar_dados()
    return "▶️ Alertas retomados!"


def cmd_ajuda(usuario, args):
    return MENU


COMANDOS = {
    "start":     cmd_start,
    "preco":     cmd_preco,
    "destinos":  cmd_destinos,
    "ativar":    cmd_ativar,
    "desativar": cmd_desativar,
    "favorito":  cmd_favorito,
    "meses":     cmd_meses,
    "meus":      cmd_meus,
    "buscar":    cmd_buscar,
    "pausar":    cmd_pausar,
    "retomar":   cmd_retomar,
    "ajuda":     cmd_ajuda,
    "help":      cmd_ajuda,
    "menu":      cmd_ajuda,
}


def processar_update(update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return
    texto = (msg.get("text") or "").strip()
    if not texto.startswith("/"):
        return

    partes = texto.split()
    cmd = partes[0][1:].split("@")[0].lower()
    args = partes[1:]

    nome = (chat.get("first_name") or "") + (" " + chat.get("last_name") if chat.get("last_name") else "")
    usuario = get_user(chat_id, nome.strip())

    handler = COMANDOS.get(cmd)
    if not handler:
        enviar_telegram(chat_id, "❓ Comando não reconhecido. Use /ajuda")
        return

    try:
        resposta = handler(usuario, args)
        if resposta:
            enviar_telegram(chat_id, resposta)
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️ Erro processando comando /{cmd}: {e}")
        enviar_telegram(chat_id, f"⚠️ Erro ao executar /{cmd}: {e}")


# ============================================================
#  LOOP DE POLLING (Telegram getUpdates)
# ============================================================

def telegram_polling():
    if not TELEGRAM_TOKEN:
        print("⚠️ TELEGRAM_TOKEN ausente — polling desativado.")
        return
    print(f"[{datetime.now()}] 📡 Iniciando polling do Telegram...")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=40)
            if r.status_code != 200:
                print(f"[{datetime.now()}] polling status {r.status_code}: {r.text[:200]}")
                time.sleep(5)
                continue
            data = r.json()
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                try:
                    processar_update(upd)
                except Exception as e:
                    print(f"[{datetime.now()}] erro update: {e}")
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ polling: {e}")
            time.sleep(5)


# ============================================================
#  SCHEDULER
# ============================================================

def scheduler_loop():
    schedule.every(VERIFICAR_HORAS).hours.do(verificar_todos)
    schedule.every().sunday.at("09:00").do(resumo_semanal)
    print(f"[{datetime.now()}] ⏰ Agendador ativo: a cada {VERIFICAR_HORAS}h + resumo dom 09:00")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ scheduler: {e}")
        time.sleep(30)


# ============================================================
#  INÍCIO
# ============================================================

def main():
    print("=" * 60)
    print(f"✈️  Monitor de Passagens PRO — {ORIGEM} → Mundo")
    print(f"    {len(DESTINOS)} destinos | Limite padrão R$ {PRECO_MAXIMO_PAD:,}")
    print(f"    🔁 Verificação a cada {VERIFICAR_HORAS}h")
    print("=" * 60)

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN ausente. Configure no Railway.")
    if not TRAVEL_TOKEN:
        print("❌ TRAVEL_TOKEN ausente. Configure no Railway.")

    carregar_dados()

    if ADMIN_CHAT_ID:
        enviar_telegram(
            ADMIN_CHAT_ID,
            "🚀 <b>Monitor PRO online!</b>\n\n"
            f"🛫 Origem: {ORIGEM}\n"
            f"🌍 Destinos disponíveis: <b>{len(DESTINOS)}</b>\n"
            f"👥 Usuários cadastrados: <b>{len(state['users'])}</b>\n"
            f"⏰ Verificação a cada {VERIFICAR_HORAS}h\n"
            f"📅 Resumo semanal: dom 09:00\n\n"
            "Peça aos novos usuários para enviar /start ao bot."
        )

    # Roda uma verificação inicial em background (se houver usuários)
    if state["users"]:
        threading.Thread(target=verificar_todos, daemon=True).start()

    # Scheduler em thread separada
    threading.Thread(target=scheduler_loop, daemon=True).start()

    # Polling em primeiro plano (mantém o processo vivo)
    telegram_polling()


if __name__ == "__main__":
    main()
