#########################
# Made by Bare (bare57) #
#########################

### Contexto
# Este bot fué hecho para otros propósitos, puede que algunas cosas sean obsoletas o pueda romperse algo en el futuro
# Usaré varios comentarios para aclarar varias cosas dentro del código, puedes borrarlos sin problema
# Para cualquier duda puedo resolverla, lo siento si parece un espaguetti xD
# Úsalo como referencia o copia-pega el código, como gustes! Espero te sirva ^^ 

### Cómo funciona?
# El evento "on_ready" prepara al bot e indica si se conectó correctamente
# Al usar el comando "set", vincula 2 canales para mandar los mismos mensajes de uno a otro, independientemente de en que canal (función "client" y "server" hacen esto, siendo "server" el canal en español)
# En ambos canales, crea 2 webhooks (Si no existen), uno en cada canal

# El bot recibe un mensaje con el evento "on_message" (O tambien desde "on_message_edit")
# Si el mensaje es de uno de los canales vinculados, hará lo siguente: (Linea 295)
    # En el canal Español traduce el mensaje al ingles y luego copia todo el contenido y viceversa 
    # Tanto @everyone y @here están filtrados, el bot necesita mencionar por lo que se tuvo que implementar una opción de filtro
    # Guarda el mensaje en la base de datos (Mira "database.py" para mas información)

# Nota, mensajes editados tambien se traducen para el otro canal, tambien como los mensajes borrados también se borran
# Nota 2: El comando "set" por ahora todos pueden usarlo, es mejor dar una restricción como "si quien lo usa no es esta persona, no hace nada"

### IMPORTANTE IR A LA LINEA 67

import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import tracemalloc
import re
tracemalloc.start()

import database as data # Esto es para la base de datos

# Constantes importantes
KEY_PATH = "KEY/.env"

# Este bot usa llama.cpp server para usar una IA local y traducir
from openai import OpenAI
ai_model = "prism-ml/Ternary-Bonsai-2-27B-gguf:PTQ1_0" # U otro modelo disponible
llama = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key= "no-key-required",
    timeout=20000.0
)

# Cargar .env
load_dotenv(KEY_PATH)

# Ajustar el bot, la variable "bot" es muy importante para decirle que hacer
intents = discord.Intents.all()
bot = commands.Bot(help_command=None, command_prefix="*", intents=intents)

# Canales, es importante para vincular los canales (channel1: Español  -  channel2: Ingles)
channels: dict[str, discord.TextChannel] = {
    "channel1": None,
    "channel2": None
}

# Evento, cuando el bot se encienda
@bot.event
async def on_ready():
    try:
        print(f"Bot conectado correctamente: {bot.application.name}")
        await bot.tree.sync() # IMPORTANTE: esto crea el comando "set", pero borra todos los demás comandos vinculados al bot, úsalo cuando se hayan puesto todos los comandos existentes

    except Exception as e:
        print(f"[ON_READY] Error: {e}")

# Evento, alguien manda un mensaje en un servidor en el que el bot está 
@bot.event
async def on_message(message: discord.Message):
    if bot.application_id == message.author.id: # Evitar repeticiones de mensajes de este bot
        return
    if message.webhook_id and message.author.discriminator == "0000": # Los webhooks si o si tienen #0000 después de su nombre, porque los bots normales tienen un "webhook_id"
        return
    
    channel1 = channels.get("channel1")
    channel2 = channels.get("channel2")
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return
    
    elif not channel1 or not channel2:
        return
    elif message.channel.id == channel1.id:
        await sent_to_channel(message, channel1, channel2)
        return
    elif message.channel.id == channel2.id:
        await sent_to_channel(message, channel2, channel1)
        return
    
@bot.event
async def on_reaction_add(reaction: discord.Reaction, member: discord.Member): # TODO: notifica por cada reaccion del otro lado aunque con el bot siga el contador en 1, es molesto
    try:
        channel1 = channels.get("channel1")
        channel2 = channels.get("channel2")
        if reaction.message.channel.id not in [channel1.id, channel2.id]:
            return
        if member.id == bot.application_id:
            return

        if reaction.message.webhook_id and reaction.message.author.discriminator == "0000":
            logs = data.get_from_web(reaction.message.id)
            channel = bot.get_channel(logs.channel_og_id) if bot.get_channel(logs.channel_og_id) else await bot.fetch_channel(logs.channel_og_id)
            message = await channel.fetch_message(logs.message_og_id)
        else:
            logs = data.get_from_og(reaction.message.id)
            channel = bot.get_channel(logs.channel_web_id) if bot.get_channel(logs.channel_web_id) else await bot.fetch_channel(logs.channel_web_id)
            message = await channel.fetch_message(logs.message_web_id)

        for react in message.reactions:
            if react.me and react.emoji == reaction.emoji: return
        await message.add_reaction(reaction.emoji)

    except Exception as e:
        print(f"[REACTION_ADD] Error: {e}")

@bot.event
async def on_reaction_remove(reaction: discord.Reaction, member: discord.Member):
    try:
        channel1 = channels.get("channel1")
        channel2 = channels.get("channel2")
        if reaction.message.channel.id not in [channel1.id, channel2.id]:
            return
        
        if member.id == bot.application_id:
            return

        if reaction.message.webhook_id and reaction.message.author.discriminator == "0000":
            logs = data.get_from_web(reaction.message.id)
            channel = bot.get_channel(logs.channel_og_id) if bot.get_channel(logs.channel_og_id) else await bot.fetch_channel(logs.channel_og_id)
            message = await channel.fetch_message(logs.message_og_id)
        else:
            logs = data.get_from_og(reaction.message.id)
            channel = bot.get_channel(logs.channel_web_id) if bot.get_channel(logs.channel_web_id) else await bot.fetch_channel(logs.channel_web_id)
            message = await channel.fetch_message(logs.message_web_id)

        for react in message.reactions:
            if react.me and react.emoji == reaction.emoji: await message.remove_reaction(reaction.emoji, member=bot.user)

    except Exception as e:
        print(f"[REACTION_REMOVE] Error: {e}")

@bot.event
async def on_message_edit(before: discord.Message, message: discord.Message): # No optimizado
    try:
        channel1 = channels.get("channel1")
        channel2 = channels.get("channel2")
        if message.channel.id not in [channel1.id, channel2.id]:
            return

        attachments: list[str] = []
        if message.id == bot.application_id:
            return

        if message.webhook_id and message.author.discriminator == "0000":
            return

        logs = data.get_from_og(before.id)
        if not logs:
            await asyncio.sleep(0.5)
            logs = data.get_from_web(before.id)
        channel = bot.get_channel(logs.channel_web_id) if bot.get_channel(logs.channel_web_id) else await bot.fetch_channel(logs.channel_web_id)
        fe_message = await channel.fetch_message(logs.message_web_id)

        content = message.content.strip()

        content = message_filter(content, message.guild)
        content_safe = content

        if content:
            if message.channel == channels["channel1"]:
                t_ori = "Spanish"
                t_tra = "English"
            else:
                t_ori = "English"
                t_tra = "Spanish"

            msg = llama.chat.completions.create(
                model=ai_model,
                messages=messages(t_ori, t_tra, content),
                store=False
            )
            content = msg.choices[0].message.content

        if message.reference:
            reference = message.reference
            re_message = reference.cached_message if reference.cached_message else await message.channel.fetch_message(reference.message_id)

            if re_message.webhook_id and re_message.author.discriminator == "0000":
                logs = data.get_from_web(re_message.id)
                if not logs:
                    await asyncio.sleep(0.5)
                    logs = data.get_from_web(re_message.id)

                if logs:
                    mention_responser = f"<@{logs.author_id}>"
                    responser = logs.message_og_url
                else:
                    mention_responser = re_message.author.name
                    responser = re_message.jump_url

            else:
                mention_responser = re_message.author.name
                if logs:
                    responser = logs.message_web_url 
                else: responser = re_message.jump_url

            re_content = logs.content if logs else re_message.content
            re_content = message_filter(" ".join(re_content.split("\n")), message.guild)
            
            if re_message.attachments or "https://" in re_content or re_content == "":
                content = f"-# Reply to {mention_responser}: [🗒️ Archivo adjunto]({responser})\n{content}"
            else:
                content = f"-# Reply to {mention_responser}: [{f"{re_content[:50]}..." if len(re_content) > 50 else re_content}]({responser})\n{content}"

        if message.attachments:
            for attach in message.attachments:
                attachments.append(attach.url)
        
        if message.stickers:
            for sticker in message.stickers:
                attachments.append(f"[{sticker.name}](https://media.discordapp.net/stickers/{sticker.id}?size=160)")

        for url in attachments:
            content += url if content == "" else f"\n-# {url}"

        if message.interaction_metadata:
            if message.interaction_metadata.type.name:
                content = f"-# {message.interaction_metadata.user.name} has used `/{message.interaction.name}`\n{content}"

        fetch_embeds = [embed for embed in message.embeds]
        for component in message.components: # Odio esto
            if isinstance(component, discord.Container):
                ctn = ""
                for children in component.children:
                    if isinstance(children, discord.SectionComponent):
                        for text in children.children:
                            if isinstance(text, discord.TextDisplay): ctn += f"\n{text.content}"
                    if isinstance(children, discord.TextDisplay):
                        ctn += f"\n{children.content}"
                fetch_embeds.append(discord.Embed(description=ctn, color=component.accent_color))

        webhook = await bot.fetch_webhook(data.get_webhook_from_channel(fe_message.channel.id))

        fe_message = await webhook.fetch_message(fe_message.id)
        await fe_message.edit(content=content, embeds=[embed for embed in message.embeds])
        data.write_update(message.channel.id, message.id, message.jump_url, fe_message.channel.id, fe_message.id, fe_message.jump_url, content_safe, message.author.id)

    except Exception as e:
        print(f"[MESSAGE_EDIT] Error: {e}")

@bot.event
async def on_message_delete(message: discord.Message):
    try:
        channel1 = channels.get("channel1")
        channel2 = channels.get("channel2")
        if message.channel.id not in [channel1.id, channel2.id]:
            return
        if message.webhook_id and message.author.discriminator == "0000":
            return
        
        logs = data.get_from_og(message.id)
        if not logs:
            await asyncio.sleep(0.5)
            logs = data.get_from_og(message.id)
        channel = bot.get_channel(logs.channel_web_id) if bot.get_channel(logs.channel_web_id) else await bot.fetch_channel(logs.channel_web_id)
        fe_message = await channel.fetch_message(logs.message_web_id)

        webhook = await bot.fetch_webhook(data.get_webhook_from_channel(fe_message.channel.id))
        fe_message = await webhook.fetch_message(fe_message.id)
        await fe_message.delete()
    
    except Exception as e:
        print(f"[MESSAGE_DELETE] Error: {e}")

# Importante filtrar para evitar pings inesperados
def message_filter(content: str, guild: discord.Guild):
    content = re.sub(r"<@!?(\d+)>", lambda m: f"@<{bot.get_user(int(m.group(1))).name}>" if bot.get_user(int(m.group(1))) else "@Usuario-Desconocido", content)
    content = re.sub(r"<@&(\d+)>", lambda m: f"@&<{guild.get_role(int(m.group(1))).name}>" if guild.get_role(int(m.group(1))) else "@Rol-Desconocido", content)
    content = content.replace("@everyone", "@<everyone>")
    content = content.replace("@here", "@<here>")
    return content.strip()

# Prompt para la IA, no es perfecto pero sirve por ahora (editable)
messages = lambda original, translate, text: [
    {"role": "system", "content": f"You are a professional {original} to {translate} translator. Your goal is to accurately convey the meaning and nuances of the original {original} text while adhering to {translate} grammar, vocabulary, and cultural sensitivities.\nProduce only the {translate} translation, without any additional explanations or commentary."},
    {"role": "user", "content": text}
]

# Esto es de lo más importante, usa el webhook para mandar el mismo mensaje al otro canal ya traducido (Tiene limitaciones, ej: no poder responder a usuarios)
async def sent_to_channel(message: discord.Message, ch_from: discord.TextChannel, ch_to: discord.TextChannel, retries: int = 0):
    try:
        if retries >= 3:
            print("Maximos intentos fallidos")
            return

        webhook = await bot.fetch_webhook(data.get_webhook_from_channel(ch_to.id))
        attachments: list[str] = []
        avatar = message.author.display_avatar if message.author.display_avatar else message.author.default_avatar
        username = f"{message.author.display_name} ({message.author.name})" if message.author.display_name else message.author.name
        content = message.content.strip()

        content_safe = content

        if content:
            if ch_from == channels["channel1"]: # t_ori y t_tra son completamente editables para otros idiomas
                t_ori = "Spanish"
                t_tra = "English"
            else:
                t_ori = "English"
                t_tra = "Spanish"

            msg = llama.chat.completions.create( # IA
                model=ai_model,
                messages=messages(t_ori, t_tra, content),
                store=False
            )
            content = msg.choices[0].message.content

        content = message_filter(content, message.guild)

        if message.reference:
            reference = message.reference
            re_message = reference.cached_message if reference.cached_message else await message.channel.fetch_message(reference.message_id)

            if re_message.webhook_id and re_message.author.discriminator == "0000":
                logs = data.get_from_web(re_message.id)
                if logs:
                    mention_responser = f"<@{logs.author_id}>"
                    responser = logs.message_og_url
                else:
                    mention_responser = re_message.author.name
                    responser = re_message.jump_url

            else:
                logs = data.get_from_og(re_message.id)
                mention_responser = re_message.author.name
                if logs:
                    responser = logs.message_web_url 
                else: responser = re_message.jump_url

            re_content = logs.content if logs else re_message.content
            re_content = message_filter(" ".join(re_content.split("\n")), message.guild)
            
            if re_message.attachments or "https://" in re_content or re_content == "":
                content = f"-# Reply to {mention_responser}: [🗒️ Archivo adjunto]({responser})\n{content}"
            else:
                content = f"-# Reply to {mention_responser}: [{f"{re_content[:50]}..." if len(re_content) > 50 else re_content}]({responser})\n{content}"

        if message.attachments:
            for attach in message.attachments:
                attachments.append(attach.url)
        
        if message.stickers:
            for sticker in message.stickers:
                attachments.append(f"[{sticker.name}](https://media.discordapp.net/stickers/{sticker.id}?size=160)")

        for url in attachments:
            content += url if content == "" else f"\n-# {url}"

        if message.interaction_metadata:
            if message.interaction_metadata.type.name:
                content = f"-# {message.interaction_metadata.user.name} has used `/{message.interaction.name}`\n{content}"

        fetch_embeds = [embed for embed in message.embeds]
        for component in message.components: # Odio esto
            if isinstance(component, discord.Container):
                ctn = ""
                for children in component.children:
                    if isinstance(children, discord.SectionComponent):
                        for text in children.children:
                            if isinstance(text, discord.TextDisplay): ctn += f"\n{text.content}"
                    if isinstance(children, discord.TextDisplay):
                        ctn += f"\n{children.content}"
                fetch_embeds.append(discord.Embed(description=ctn, color=component.accent_color))

        response = await webhook.send(content=content, username=username, embeds=fetch_embeds, avatar_url=avatar.url.replace(".gif?", ".png?"), wait=True)
        data.write(message.channel.id, message.id, message.jump_url, response.channel.id, response.id, response.jump_url, content_safe, message.author.id, "normal", round(message.created_at.timestamp()))

    except discord.NotFound:
        await sent_to_channel(message, ch_from, ch_to, retries+1)
        await server()
        await client()
        return

    except Exception as e:
        print(f"[SENT] Error: {e}")    

class SameChannelsError(Exception):
    pass

# Comando de prueba, importante para vincular los canales
@bot.tree.command(name="set", description="[DEBUG] Une ambos canales para enviar los mensajes al otro canal")
@discord.app_commands.describe(spanish_channel="El canal en español", english_channel="El canal en ingles")
async def set(interaction: discord.Interaction, spanish_channel: discord.TextChannel, english_channel: discord.TextChannel):
    try:
        channels["channel1"] = spanish_channel
        await server()
        channels["channel2"] = english_channel
        await client()
        await interaction.response.send_message("Los canales han sido cambiados con éxito", ephemeral=True)
    except SameChannelsError:
        await interaction.response.send_message("Los canales **deben** ser diferentes", ephemeral=True)


### Cosas importantes
async def server(retries: int = 0):
    while True:
        if retries >= 3:
            print("[SERVER] Máximos intentos alcanzados")
            break

        channel1 = channels.get("channel1") 

        try:
            web = data.get_webhook_from_channel(channel1.id)
            if not web:
                webhook = await channel1.create_webhook(name="Bare_Translator", reason="Bot necesario para el funcionamiento del Translator")
                data.set_webhook(channel1.id, webhook.id)
            else:
                try:
                    await bot.fetch_webhook(web)
                except discord.NotFound:
                    webhook = await channel1.create_webhook(name="Bare_Translator", reason="Bot necesario para el funcionamiento del Translator")
                    data.update_webhook(channel1.id, webhook.id)
            break
        except Exception as e:
            print("Selecciona una ID válida", e)
            retries += 1
            continue

async def client(retries: int = 0):
    while True:
        if retries >= 3:
            print("[SERVER] Máximos intentos alcanzados")
            break
        
        channel2 = channels.get("channel2")
        
        if channel2 == channels.get("channel1"):
            raise SameChannelsError()
        try:

            web = data.get_webhook_from_channel(channel2.id)
            if not web:
                webhook = await channel2.create_webhook(name="Bare_Translator", reason="Bot necesario para el funcionamiento del Translator")
                data.set_webhook(channel2.id, webhook.id)
            else:
                try:
                    await bot.fetch_webhook(web)
                except discord.NotFound:
                    webhook = await channel2.create_webhook(name="Bare_Translator", reason="Bot necesario para el funcionamiento del Translator")
                    data.update_webhook(channel2.id, webhook.id)
            break

        except Exception as e:
            print("Selecciona una ID válida", e)
            retries += 1
            continue

# Inicia el bot y lo activa
async def main():
    import os
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())