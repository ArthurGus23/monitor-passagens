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

ORIGEM           = "GRU"    # Guarulhos
PRECO_MAXIMO     = 4000    # R$
VERIFICAR_HORAS  = 3       # a cada 3 horas

# ============================================================
#  DESTINOS MONITORADOS
# ============================================================
DESTINOS = [
    # ⭐ FOCO PRINCIPAL
    ("DUB", "Dublin, Irlanda",            "🇮🇪"),

    # 🌍 EUROPA
    ("BER", "Berlim, Alemanha",           "🇩🇪"),
    ("CDG", "Paris, França",              "🇫🇷"),
    ("LHR", "Londres, Reino Unido",       "🇬🇧"),
    ("MAD", "Madri, Espanha",             "🇪🇸"),
    ("FCO", "Roma, Itália",               "🇮🇹"),
    ("AMS", "Amsterdã, Holanda",          "🇳🇱"),
    ("VIE", "Viena, Áustria",             "🇦🇹"),
    ("PRG", "Praga, Rep. Tcheca",         "🇨🇿"),
    ("WAW", "Varsóvia, Polônia",          "🇵🇱"),
    ("BUD", "Budapeste, Hungria",         "🇭🇺"),
    ("ATH", "Atenas, Grécia",             "🇬🇷"),            
    ("CPH", "Copenhague, Dinamarca",      "🇩🇰"),
    ("OSL", "Oslo, Noruega",              "🇳🇴"),
    ("ARN", "Estocolmo, Suécia",          "🇸🇪"),
    ("HEL", "Helsinki, Finlândia",        "🇫🇮"),
    ("TLL", "Tallinn, Estônia",           "🇪🇪"),
    ("SVO", "Moscou, Rússia",             "🇷🇺"),
    ("IST", "Istambul, Turquia",          "🇹🇷"),
    ("OTP", "Bucareste, Romênia",         "🇷🇴"),
    ("BEG", "Belgrado, Sérvia",           "🇷🇸"),
    ("RIX", "Riga, Letônia",              "🇱🇻"),
    ("VNO", "Vilnius, Lituânia",          "🇱🇹"),
    ("TBS", "Tbilisi, Geórgia",           "🇬🇪"),

    # 🌎 AMÉRICAS
    ("EZE", "Buenos Aires, Argentina",    "🇦🇷"),
    ("MEX", "Cidade do México, México",   "🇲🇽"),
    ("IAD", "Washington D.C., EUA",       "🇺🇸"),
    ("JFK", "Nova York, EUA",             "🇺🇸"),
    ("LAX", "Los Angeles, EUA",           "🇺🇸"),
    ("YOW", "Ottawa, Canadá",             "🇨🇦"),
    ("SCL", "Santiago, Chile",            "🇨🇱"),
    ("LIM", "Lima, Peru",                 "🇵🇪"),
    ("BOG", "Bogotá, Colômbia",           "🇨🇴"),
    ("MVD", "Montevidéu, Uruguai",        "🇺🇾"),
    ("PTY", "Cidade do Panamá, Panamá",   "🇵🇦"),
    ("HAV", "Havana, Cuba",               "🇨🇺"),

    # 🌏 ÁSIA
    ("NRT", "Tóquio, Japão",              "🇯🇵"),
    ("PEK", "Pequim, China",              "🇨🇳"),
    ("ICN", "Seul, Coreia do Sul",        "🇰🇷"),
    ("DEL", "Nova Delhi, Índia",          "🇮🇳"),
    ("BKK", "Bangkok, Tailândia",         "🇹🇭"),
    ("SIN", "Singapura",                  "🇸🇬"),
    ("KUL", "Kuala Lumpur, Malásia",      "🇲🇾"),
    ("CGK", "Jacarta, Indonésia",         "🇮🇩"),
    ("MNL", "Manila, Filipinas",          "🇵🇭"),
    ("HAN", "Hanói, Vietnã",              "🇻🇳"),
    ("DXB", "Dubai, Emirados Árabes",     "🇦🇪"),
    ("TLV", "Tel Aviv, Israel",           "🇮🇱"),
    ("ISB", "Islamabade, Paquistão",      "🇵🇰"),
    ("TAS", "Tashkent, Uzbequistão",      "🇺🇿"),

    # 🌍 ÁFRICA
    ("CAI", "Cairo, Egito",               "🇪🇬"),
    ("NBO", "Nairóbi, Quênia",            "🇰🇪"),
    ("JNB", "Joanesburgo, África do Sul", "🇿🇦"),
    ("LOS", "Lagos, Nigéria",             "🇳🇬"),
    ("ACC", "Acra, Gana",                 "🇬🇭"),
    ("CMN", "Casablanca, Marrocos",       "🇲🇦"),
    ("ADD", "Adis Abeba, Etiópia",        "🇪🇹"),
    ("LAD", "Luanda, Angola",             "🇦🇴"),
    ("MPM", "Maputo, Moçambique",         "🇲🇿"),

    # 🌏 OCEANIA
    ("SYD", "Sydney, Austrália",          "🇦🇺"),
    ("AKL", "Auckland, Nova Zelândia",    "🇳🇿"),
]

# ============================================================
#  FUNÇÕES
# ============================================================

DESTINATARIOS = [
    TELEGRAM_CHAT_ID,   # você
    "6170699300",       # amigo 1
    "5938670130",       # amigo 2
]

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
def buscar_melhor_oferta(codigo_iata, nome_cidade, emoji):
    """
    Usa a Flight Data API (v2/prices/month-matrix) — disponível no plano gratuito.
    Retorna os preços mínimos por mês para a rota, sem precisar de data exata.
    """
    melhor = None
    try:
        url = "https://api.travelpayouts.com/v2/prices/month-matrix"
        params = {
            "origin":      ORIGEM,
            "destination": codigo_iata,
            "currency":    "brl",
            "show_to_affiliates": "true",
            "token":       TRAVEL_TOKEN
        }
        r = requests.get(url, params=params, timeout=15)
        print(f"  [{codigo_iata}] status={r.status_code}")

        if r.status_code == 200:
            dados = r.json()
            # A API retorna lista em dados["data"]
            lista = dados.get("data") or []
            for item in lista:
                preco = item.get("price", 999999)
                if preco <= PRECO_MAXIMO:
                    if melhor is None or preco < melhor["preco"]:
                        melhor = {
                            "destino":    nome_cidade,
                            "emoji":      emoji,
                            "preco":      preco,
                            "data_ida":   item.get("depart_date", "—"),
                            "data_volta": item.get("return_date", "—"),
                            "cia":        item.get("airline", "—"),
                            "link":       item.get("link", "")
                        }
        else:
            print(f"  [{codigo_iata}] Resposta: {r.text[:200]}")

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

    print(f"[{datetime.now()}] 📊 {len(ofertas)} oferta(s) encontrada(s) abaixo de R${PRECO_MAXIMO}.")

    if not ofertas:
        enviar_telegram(
            f"🔍 <b>Verificação concluída</b>\n\n"
            f"Nenhuma passagem abaixo de R$ {PRECO_MAXIMO:,} no momento.\n"
            f"Próxima verificação em {VERIFICAR_HORAS}h. ⏰"
        )
        return

    ofertas.sort(key=lambda x: x["preco"])
    tallinn = next((o for o in ofertas if "Tallinn" in o["destino"]), None)
    outras  = [o for o in ofertas if "Tallinn" not in o["destino"]]

    msg = (
        f"✈️ <b>ALERTAS DE PASSAGENS</b>\n"
        f"🗓 {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
        f"💰 Limite: R$ {PRECO_MAXIMO:,} | {len(ofertas)} oferta(s)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if tallinn:
        msg += (
            f"⭐ <b>DESTINO PRINCIPAL</b>\n"
            f"{tallinn['emoji']} <b>{tallinn['destino']}</b>\n"
            f"   💵 <b>R$ {tallinn['preco']:,.0f}</b>\n"
            f"   📅 Ida: {tallinn['data_ida']} | Volta: {str(tallinn['data_volta'])[:10]}\n"
            f"   🏢 {tallinn['cia']}\n"
        )
        if tallinn.get("link"):
            msg += f"   🔗 <a href='https://www.aviasales.com{tallinn['link']}'>Ver passagem</a>\n"
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"

    if outras:
        msg += f"🌍 <b>OUTRAS OFERTAS</b>\n\n"
        for o in outras[:10]:
            msg += f"{o['emoji']} <b>{o['destino']}</b> — R$ {o['preco']:,.0f}\n"
            msg += f"   📅 {o['data_ida']} | 🏢 {o['cia']}\n"
            if o.get("link"):
                msg += f"   🔗 <a href='https://www.aviasales.com{o['link']}'>Ver</a>\n"
            msg += "\n"
        if len(outras) > 10:
            msg += f"<i>+{len(outras)-10} outras ofertas encontradas.</i>\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n🤖 Monitor automático de passagens"
    enviar_telegram(msg)
    print(f"[{datetime.now()}] ✅ Alertas enviados no Telegram!")


# ============================================================
#  INÍCIO
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print(f"✈️  Monitor de Passagens — VDC → Mundo todo")
    print(f"    {len(DESTINOS)} destinos | Limite R$ {PRECO_MAXIMO:,}")
    print("=" * 55)

    # Testa conexão com Telegram logo de cara
    enviar_telegram(
        "🚀 <b>Monitor de passagens iniciado!</b>\n\n"
        f"🛫 Origem: Guarulhos (GRU)\n"
        f"🌍 Destinos monitorados: <b>{len(DESTINOS)} capitais</b>\n"
        f"⭐ Foco principal: Tallinn, Estônia 🇪🇪\n"
        f"💰 Alerta se preço ≤ R$ {PRECO_MAXIMO:,}\n"
        f"🕐 Verificação a cada {VERIFICAR_HORAS}h\n\n"
        "Você receberá alertas das melhores ofertas! ✅"
    )

    verificar_todos()
    schedule.every(VERIFICAR_HORAS).hours.do(verificar_todos)

    print(f"\n⏰ Próxima verificação em {VERIFICAR_HORAS} horas.")
    print("Deixe rodando. Ctrl+C para parar.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)
