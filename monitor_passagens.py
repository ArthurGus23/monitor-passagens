import requests
import time
import schedule
from datetime import datetime, timedelta
import os

# ============================================================
#  CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TRAVEL_TOKEN     = os.getenv("TRAVEL_TOKEN")

ORIGEM          = "GRU"   # São Paulo (hub principal)
PRECO_MAXIMO    = 20000   # R$
VERIFICAR_HORAS = 6       # a cada 6 horas

# Todos os destinatários
DESTINATARIOS = [
    TELEGRAM_CHAT_ID,
    "6170699300",
    "5938670130",
]

# ============================================================
#  DESTINOS MONITORADOS
# ============================================================
DESTINOS = [
    # ⭐ FOCO PRINCIPAL — Dublin → Estônia
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

# ============================================================
#  FUNÇÕES
# ============================================================

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in DESTINATARIOS:
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "HTML"
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                print(f"[{datetime.now()}] ✅ Enviado para {chat_id}!")
            else:
                print(f"[{datetime.now()}] ❌ Erro para {chat_id}: {r.text}")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Erro de conexão {chat_id}: {e}")
        time.sleep(0.3)


def montar_link_kayak(origem, destino, data_ida, data_volta):
    """Monta link direto do Kayak com origem, destino e data."""
    try:
        # Formata datas no padrão do Kayak: AAAA-MM-DD
        ida = data_ida if data_ida and data_ida != "—" else ""
        volta = data_volta if data_volta and data_volta != "—" else ""

        if ida and volta:
            return f"https://www.kayak.com.br/flights/{origem}-{destino}/{ida}/{volta}"
        elif ida:
            return f"https://www.kayak.com.br/flights/{origem}-{destino}/{ida}"
        else:
            return f"https://www.kayak.com.br/flights/{origem}-{destino}"
    except:
        return f"https://www.kayak.com.br/flights/{origem}-{destino}"


def buscar_melhor_oferta(codigo_iata, nome_cidade, emoji):
    melhor = None
    try:
        url = "https://api.travelpayouts.com/v2/prices/month-matrix"
        params = {
            "origin":             ORIGEM,
            "destination":        codigo_iata,
            "currency":           "brl",
            "show_to_affiliates": "true",
            "token":              TRAVEL_TOKEN
        }
        r = requests.get(url, params=params, timeout=15)
        print(f"  [{codigo_iata}] status={r.status_code}")

        if r.status_code == 200:
            lista = r.json().get("data") or []
            for item in lista:
                preco = item.get("value", 999999)
                if preco <= PRECO_MAXIMO:
                    if melhor is None or preco < melhor["preco"]:
                        data_ida   = item.get("depart_date", "")
                        data_volta = item.get("return_date", "")
                        melhor = {
                            "destino":    nome_cidade,
                            "emoji":      emoji,
                            "preco":      preco,
                            "data_ida":   data_ida or "—",
                            "data_volta": data_volta or "—",
                            "cia":        item.get("gate", "—"),
                            "link":       montar_link_kayak(ORIGEM, codigo_iata, data_ida, data_volta)
                        }
        time.sleep(0.5)

    except Exception as e:
        print(f"  ⚠️ Erro em {nome_cidade}: {e}")

    return melhor


def verificar_todos():
    total = len(DESTINOS)
    print(f"\n[{datetime.now()}] 🔍 Iniciando verificação de {total} destinos...")
    ofertas = []

    for i, (cod, nome, emoji) in enumerate(DESTINOS, 1):
        print(f"  [{i}/{total}] {nome}...")
        oferta = buscar_melhor_oferta(cod, nome, emoji)
        if oferta:
            ofertas.append(oferta)

    print(f"[{datetime.now()}] 📊 {len(ofertas)} oferta(s) encontrada(s).")

    if not ofertas:
        enviar_telegram(
            f"🔍 <b>Verificação concluída</b>\n\n"
            f"Nenhuma passagem abaixo de R$ {PRECO_MAXIMO:,} no momento.\n"
            f"Próxima verificação em {VERIFICAR_HORAS}h. ⏰"
        )
        return

    ofertas.sort(key=lambda x: x["preco"])

    dublin = next((o for o in ofertas if "Dublin" in o["destino"]), None)
    hubs   = [o for o in ofertas if "hub" in o["destino"] and "Dublin" not in o["destino"]]
    outras = [o for o in ofertas if "hub" not in o["destino"] and "Dublin" not in o["destino"]]

    msg = (
        f"✈️ <b>ALERTAS DE PASSAGENS</b>\n"
        f"🗓 {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
        f"💰 Limite: R$ {PRECO_MAXIMO:,} | {len(ofertas)} oferta(s)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if dublin:
        msg += (
            f"⭐ <b>FOCO PRINCIPAL — GATEWAY ESTÔNIA</b>\n"
            f"{dublin['emoji']} <b>{dublin['destino']}</b>\n"
            f"   💵 <b>R$ {dublin['preco']:,.0f}</b>\n"
            f"   📅 Ida: {dublin['data_ida']}\n"
            f"   🏢 {dublin['cia']}\n"
            f"   💡 De Dublin → Tallinn por ~€50-150\n"
            f"   🔗 <a href='{dublin['link']}'>Buscar no Kayak</a>\n"
        )
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"

    if hubs:
        msg += f"🔵 <b>HUBS COM VOO PARA TALLINN</b>\n\n"
        for o in hubs:
            msg += f"{o['emoji']} <b>{o['destino']}</b> — R$ {o['preco']:,.0f}\n"
            msg += f"   📅 {o['data_ida']} | 🏢 {o['cia']}\n"
            msg += f"   🔗 <a href='{o['link']}'>Buscar no Kayak</a>\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    if outras:
        msg += f"🌍 <b>OUTRAS OFERTAS</b>\n\n"
        for o in outras[:8]:
            msg += f"{o['emoji']} <b>{o['destino']}</b> — R$ {o['preco']:,.0f}\n"
            msg += f"   📅 {o['data_ida']} | 🏢 {o['cia']}\n"
            msg += f"   🔗 <a href='{o['link']}'>Buscar no Kayak</a>\n\n"
        if len(outras) > 8:
            msg += f"<i>+{len(outras)-8} outras ofertas encontradas.</i>\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Monitor automático de passagens"
    enviar_telegram(msg)
    print(f"[{datetime.now()}] ✅ Alertas enviados!")


# ============================================================
#  INÍCIO
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print(f"✈️  Monitor de Passagens — GRU → Mundo todo")
    print(f"    {len(DESTINOS)} destinos | Limite R$ {PRECO_MAXIMO:,}")
    print(f"    ⭐ Foco: Dublin → Estônia")
    print("=" * 55)

    enviar_telegram(
        "🚀 <b>Monitor de passagens atualizado!</b>\n\n"
        f"🛫 Origem: São Paulo (GRU)\n"
        f"🌍 Destinos monitorados: <b>{len(DESTINOS)} cidades</b>\n"
        f"⭐ Foco principal: Dublin 🇮🇪 → Estônia 🇪🇪\n"
        f"🔵 Hubs: FRA, IST, ARN, HEL, RIX, WAW\n"
        f"💰 Alerta se preço ≤ R$ {PRECO_MAXIMO:,}\n"
        f"🔗 Links diretos via Kayak\n"
        f"🕐 Verificação a cada {VERIFICAR_HORAS}h\n\n"
        "Alertas chegando para 3 usuários! ✅"
    )

    verificar_todos()
    schedule.every(VERIFICAR_HORAS).hours.do(verificar_todos)

    print(f"\n⏰ Próxima verificação em {VERIFICAR_HORAS} horas.")
    print("Deixe rodando. Ctrl+C para parar.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)
