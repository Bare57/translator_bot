import sqlite3 as sql

## Este archivo sirve para conectar el bot con la base de datos en "data/log.db"
# Existen 2 tablas, uno para los webhooks (No implementado por falta de tiempo) y otro para los mensajes
# ¿Por qué una base de datos para los mensajes? Se necesita para sincronizar los mensajes y las respuestas
    # Cuando lo pruebas y lo usas, ves que las respuestas desde el webhook te mandan al mensaje del mismo canal en lugar del original (si la respuesta es hacia un webhook)
    # Esto es para mantener el chat en un solo canal en lugar de tener que ir al otro, así también el webhook mantiene la esencia de que es solo un canal en donde se habla

DATA_PATH = "data/log.db"

# No recomendado cambiar todo lo que está abajo, hazlo bajo tu propio riesgo

conn = sql.connect(DATA_PATH)
cursor = conn.cursor()
cursor.execute("""--sql
    CREATE TABLE if NOT EXISTS [webhook] (
        channel_id VARCHAR(20) primary key,
        webhook_id VARCHAR(20) null
    )""")
conn.commit()
cursor.execute("""--sql
    CREATE TABLE if NOT EXISTS [logs] (
        channel_og_id VARCHAR(20),
        message_og_id VARCHAR(20),
        message_og_url TEXT,
        channel_web_id VARCHAR(20),
        message_web_id VARCHAR(20),
        message_web_url TEXT,
        content TEXT,
        author_id VARCHAR(20),
        status TEXT default 'normal',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
conn.commit()
conn.close()

def set_webhook(channel_id, webhook_id):
    """Guarda la Webhook de un canal en específico para un futuro uso"""
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO [webhook](channel_id, webhook_id) VALUES (?, ?)", (channel_id, webhook_id,))
    conn.commit()
    conn.close()

def update_webhook(channel_id, webhook_id):
    """Guarda la Webhook de un canal en específico para un futuro uso"""
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE [webhook] SET webhook_id = ? where channel_id = ?", (webhook_id, channel_id,))
    conn.commit()
    conn.close()

def get_webhook_from_channel(channel_id):
    """Obtiene la ID del Webhook de un canal en específico, si no existe será None en su lugar"""
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT webhook_id from [webhook] where channel_id = ?", (channel_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def write(channel_og_id, message_og_id, message_og_url, channel_web_id, message_web_id, message_web_url, content, author_id, status, timestamp):
    """Escribe en la base de datos la ubicación del mensaje original y referente"""
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO [logs](channel_og_id, message_og_id, message_og_url, channel_web_id, message_web_id, message_web_url, content, author_id, status, timestamp) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (channel_og_id, message_og_id, message_og_url, channel_web_id, message_web_id, message_web_url, content, author_id, status, timestamp,))
    conn.commit()
    conn.close()

def write_update(channel_og_id, message_og_id, message_og_url, channel_web_id, message_web_id, message_web_url, content, author_id):
    """Actualiza en la base de datos la ubicación del mensaje original y referente"""
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE [logs] SET channel_og_id = ?, message_og_id = ?, message_og_url = ?, channel_web_id = ?, message_web_id = ?, message_web_url = ?, content = ?, author_id = ? where message_og_id = ?", (channel_og_id, message_og_id, message_og_url, channel_web_id, message_web_id, message_web_url, content, author_id, message_og_id,))
    conn.commit()
    conn.close()


class Logs:
    def __init__(self, fetch: list):
        self.channel_og_id = fetch[0]
        self.message_og_id = fetch[1]
        self.message_og_url = fetch[2]
        self.channel_web_id = fetch[3]
        self.message_web_id = fetch[4]
        self.message_web_url = fetch[5]
        self.content = fetch[6]
        self.author_id = fetch[7]
        self.status = fetch[8]
        self.timestamp = fetch[9]


def get_from_og(og_message_id) -> Logs:
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM [logs] where message_og_id = ?", (og_message_id,))
    result = cursor.fetchone()
    return Logs(result) if result else None

def get_from_web(web_message_id) -> Logs:
    conn = sql.connect(DATA_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM [logs] where message_web_id = ?", (web_message_id,))
    result = cursor.fetchone()
    return Logs(result) if result else None