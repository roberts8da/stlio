#!/usr/bin/env python3

import os
import base64
import random
import string
import asyncio
import logging
import threading
from pathlib import Path

import httpx
import discord
from discord import Intents, Client
from flask import Flask, request, jsonify, send_from_directory, session
from flask_session import Session


def get_port():
    for env_var in ['SERVER_PORT', 'PORT', 'APP_PORT', 'ALLOCATED_PORT']:
        val = os.environ.get(env_var)
        if val:
            try:
                return int(val)
            except ValueError:
                pass
    print('💡 Tip: Set the environment variable PORT=your_port in the "Startup Parameters" of the EkNodes panel')
    return 443

PORT = get_port()

CONFIG_FILE = './.npm/sub.txt'

def generate_random_password(length=16):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def generate_example_token():
    chars = string.ascii_letters + string.digits
    part1 = base64.b64encode(str(random.random()).encode()).decode()[:24]
    part2 = ''.join(random.choices(chars, k=6))
    part3 = ''.join(random.choices(chars, k=27))
    return f'{part1}.{part2}.{part3}'

config = {
    'adminPassword':      generate_random_password(16),
    'discordToken':       generate_example_token(),
    'translateApiUrl':    'https://libretranslate.com',
    'translateApiKey':    '',
    'botStatus':          'offline',
    'commandPrefix':      '!',
    'supportedLanguages': ['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru']
}

def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f.read().splitlines():
                    if '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip()
                        if key == 'supportedLanguages':
                            config[key] = [lang.strip() for lang in value.split(',')]
                        else:
                            config[key] = value
            print('✅ Configuration file loaded successfully')
        else:
            print('📝 First startup, generating new config file')
            print('🔑 Generated admin password:', config['adminPassword'])
            print('🎫 Generated sample Token:', config['discordToken'])
            save_config()
    except Exception as e:
        print('❌ Failed to read config file:', str(e))

def save_config():
    try:
        dir_path = os.path.dirname(CONFIG_FILE)
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        lines = [
            f"adminPassword={config['adminPassword']}",
            f"discordToken={config['discordToken']}",
            f"translateApiUrl={config['translateApiUrl']}",
            f"translateApiKey={config['translateApiKey']}",
            f"botStatus={config['botStatus']}",
            f"commandPrefix={config['commandPrefix']}",
            f"supportedLanguages={','.join(config['supportedLanguages'])}"
        ]
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print('💾 Configuration saved')
    except Exception as e:
        print('❌ Failed to save config file:', str(e))

load_config()

discord_client = None
discord_loop   = None

async def translate_text(text, target_lang='zh', source_lang='auto'):
    url = f"{config['translateApiUrl']}/translate"
    headers = {'Content-Type': 'application/json'}
    if config.get('translateApiKey'):
        headers['Authorization'] = f"Bearer {config['translateApiKey']}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, json={
                'q': text, 'source': source_lang,
                'target': target_lang, 'format': 'text'
            }, headers=headers)
            return res.json().get('translatedText')
    except Exception as e:
        print('Translation error:', str(e))
        return None

async def detect_language(text):
    url = f"{config['translateApiUrl']}/detect"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, json={'q': text})
            return res.json()[0].get('language', 'en')
    except Exception as e:
        print('Language detection error:', str(e))
        return 'en'

def start_bot():
    global discord_client, discord_loop

    if not config.get('discordToken'):
        print('⚠️  Discord Token not configured')
        return False

    try:
        intents = Intents.default()
        intents.message_content = True
        intents.guild_messages   = True

        discord_client = Client(intents=intents)

        @discord_client.event
        async def on_ready():
            print(f'✅ Bot is online: {discord_client.user}')
            config['botStatus'] = 'online'
            save_config()

        @discord_client.event
        async def on_message(message):
            if message.author.bot:
                return
            content = message.content.strip()
            prefix  = config['commandPrefix']

            if content.startswith(f'{prefix}translate ') or content.startswith(f'{prefix}tr '):
                offset = len(prefix) + (10 if content.startswith(f'{prefix}translate ') else 3)
                args = content[offset:].strip().split(' ')

                if len(args) < 2:
                    await message.reply(f'❌ Usage: `{prefix}translate <target_language> <text>`')
                    return

                target_lang       = args[0].lower()
                text_to_translate = ' '.join(args[1:])

                await message.channel.typing()
                translated = await translate_text(text_to_translate, target_lang)

                if translated:
                    detected = await detect_language(text_to_translate)
                    embed = discord.Embed(title='🌍 Translation Result', color=0x5865F2)
                    embed.add_field(name=f'Original ({detected})',      value=text_to_translate, inline=False)
                    embed.add_field(name=f'Translated ({target_lang})', value=translated,        inline=False)
                    embed.set_footer(text='Translation Bot')
                    await message.reply(embed=embed)
                else:
                    await message.reply('❌ Translation failed, please try again later.')

            if content == f'{prefix}help':
                embed = discord.Embed(title='🤖 Translation Bot Usage Guide', color=0x5865F2)
                embed.add_field(
                    name='📌 Basic Command',
                    value=f'`{prefix}translate <language> <text>` or `{prefix}tr <language> <text>`',
                    inline=False
                )
                embed.add_field(
                    name='🌐 Supported Languages',
                    value=', '.join(config['supportedLanguages']),
                    inline=False
                )
                embed.add_field(name='💡 Example', value=f'`{prefix}tr zh Hello world`', inline=False)
                await message.reply(embed=embed)

        def run():
            global discord_loop
            discord_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(discord_loop)
            discord_loop.run_until_complete(discord_client.start(config['discordToken']))

        t = threading.Thread(target=run, daemon=True)
        t.start()
        return True

    except Exception as e:
        print('❌ Bot failed to start:', str(e))
        config['botStatus'] = 'error'
        return False

def stop_bot():
    global discord_client, discord_loop
    if discord_client and discord_loop:
        asyncio.run_coroutine_threadsafe(discord_client.close(), discord_loop)
        discord_client = None
        config['botStatus'] = 'offline'
        save_config()
        print('🛑 Bot stopped')

async def get_public_ip():
    async with httpx.AsyncClient(timeout=3) as client:
        for url in ['https://api.ip.sb/ip', 'https://api.ipify.org']:
            try:
                res = await client.get(url)
                ip = res.text.strip()
                if ip:
                    return ip
            except Exception:
                pass
    return None

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask.app').setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = 'discord-bot-secret-key'
app.config['SESSION_TYPE']               = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
Session(app)

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'panel.html')

@app.get('/api/auth/check')
def auth_check():
    return jsonify({'isAdmin': session.get('isAdmin', False)})

@app.post('/api/auth/login')
def auth_login():
    data = request.get_json() or {}
    if data.get('password') == config['adminPassword']:
        session['isAdmin'] = True
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.post('/api/auth/logout')
def auth_logout():
    session.clear()
    return jsonify({'success': True})

@app.post('/api/auth/change-password')
def change_password():
    if not session.get('isAdmin'):
        return jsonify({'success': False}), 403
    data = request.get_json() or {}
    new_pw = data.get('newPassword', '')
    if len(new_pw) >= 6:
        config['adminPassword'] = new_pw
        save_config()
        session.clear()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.get('/api/config')
def get_config():
    return jsonify(config)

@app.post('/api/config')
def post_config():
    if not session.get('isAdmin'):
        return jsonify({'success': False}), 403
    data = request.get_json() or {}
    config['discordToken']       = data.get('discordToken', '')
    config['translateApiUrl']    = data.get('translateApiUrl', 'https://libretranslate.com')
    config['translateApiKey']    = data.get('translateApiKey', '')
    config['commandPrefix']      = data.get('commandPrefix', '!')
    config['supportedLanguages'] = [l.strip() for l in data.get('supportedLanguages', '').split(',')]
    save_config()
    return jsonify({'success': True})

@app.post('/api/bot/start')
def api_start_bot():
    if not session.get('isAdmin'):
        return jsonify({'success': False}), 403
    if start_bot():
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Please configure the Discord Token first'})

@app.post('/api/bot/stop')
def api_stop_bot():
    if not session.get('isAdmin'):
        return jsonify({'success': False}), 403
    stop_bot()
    return jsonify({'success': True})

def print_startup_banner(public_ip):
    if public_ip:
        print(f'✅ Public IP detected: {public_ip}')
    else:
        print('⚠️  Unable to retrieve public IP, using localhost')
    print('')
    print('╔════════════════════════════════════════════════════════╗')
    print('║        🤖 Discord Translation Bot Panel Started        ║')
    print('╚════════════════════════════════════════════════════════╝')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print('🔐 Login Credentials (keep them safe)')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f"   Admin password: {config['adminPassword']}")
    print(f"   Sample Token: {config['discordToken'][:30]}...")
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print('💡 Tips:')
    print('   1. Use the admin password above for your first login')
    print('   2. After logging in, enter your real Discord Bot Token in the panel')
    print('   3. It is recommended to change the admin password in "Security Settings"')
    print('   4. Configuration is saved in the .npm/sub.txt file')
    print('')

async def startup():
    print('🔍 Fetching public IP address...')
    public_ip = await get_public_ip()
    print_startup_banner(public_ip)

    token = config.get('discordToken', '')
    if token and len(token) > 50 and 'example' not in token and config.get('botStatus') == 'online':
        print('🚀 Token detected, starting bot...')
        start_bot()

    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=PORT, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

if __name__ == '__main__':
    asyncio.run(startup())
    threading.Event().wait()
