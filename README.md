# 🤖 Discord Translation Bot

A powerful, lightweight Discord bot with a built-in web management panel — translate messages across **8+ languages** in real time, all managed through a clean browser UI. No coding knowledge required to operate.

---

## ✨ Features

- 🌍 **Real-time translation** powered by LibreTranslate — self-hostable and privacy-friendly
- 🔍 **Auto language detection** — no need to specify the source language
- 🖥️ **Web management panel** — start/stop the bot, configure tokens, change passwords, all from your browser
- 🔐 **Password-protected admin panel** — secure by default with a randomly generated password on first launch
- 💾 **Persistent configuration** — all settings saved to disk, survive restarts
- ⚡ **Zero downtime config updates** — change settings live without restarting the server
- 🎨 **Beautiful Discord embeds** — translation results are presented in clean, readable embed cards
- 🛠️ **Prefix customizable** — change the command prefix to anything you like

---

## 🌐 Supported Languages (Default)

| Code | Language |
|------|----------|
| `zh` | Chinese |
| `en` | English |
| `ja` | Japanese |
| `ko` | Korean |
| `fr` | French |
| `de` | German |
| `es` | Spanish |
| `ru` | Russian |

> You can add or remove languages at any time from the web panel.

---

## 🚀 Deployment (EkNodes / Pterodactyl Panel)

This project is designed to run out of the box on **EkNodes** and any **Pterodactyl-compatible** hosting panel using the startup command below.

### 📋 Requirements

- Python 3.10+
- A `requirements.txt` file in your container root
- A Discord Bot Token ([create one here](https://discord.com/developers/applications))
- A LibreTranslate API endpoint (public: `https://libretranslate.com` or self-hosted)

### 📦 `requirements.txt`

```
discord.py
flask
flask-session
httpx
```

### ▶️ Startup Command

Paste this into the **Startup Command** field in your EkNodes / Pterodactyl panel:

```bash
if [[ -d .git ]] && [[ "0" == "1" ]]; then git pull; fi; if [[ ! -z "" ]]; then pip install -U --prefix .local ; fi; if [[ -f /home/container/${REQUIREMENTS_FILE} ]]; then pip install -U --prefix .local -r ${REQUIREMENTS_FILE}; fi; /usr/local/bin/python /home/container/app.py
```

### 🔧 Environment Variables

Set these in the **Startup Parameters** section of your panel:

| Variable | Description | Example |
|----------|-------------|---------|
| `SERVER_PORT` | Port the web panel listens on | `10041` |
| `REQUIREMENTS_FILE` | Path to your requirements file | `requirements.txt` |

> 💡 If no port variable is set, the app defaults to port `443`.

---

## 🖥️ First Launch

Once the container starts, you'll see output like this in the console:

```
📝 First startup, generating new config file
🔑 Generated admin password: xxxxxxxxxxxxxxxx
🎫 Generated sample Token: xxxxxxxx...
🔍 Fetching public IP address...
✅ Public IP detected: x.x.x.x

╔════════════════════════════════════════════════════════╗
║        🤖 Discord Translation Bot Panel Started        ║
╚════════════════════════════════════════════════════════╝
   Admin password: xxxxxxxxxxxxxxxx
```

1. 🌐 Open your browser and navigate to `http://<your-server-ip>:<port>`
2. 🔐 Log in using the **admin password** shown in the console
3. 🎫 Enter your **Discord Bot Token** in the configuration panel
4. ▶️ Click **Start Bot** — your bot is now live on Discord!
5. 🔑 Go to **Security Settings** and change your admin password

> ⚠️ The generated password and sample token are printed only on first launch. Save them immediately, or retrieve them from `.npm/sub.txt`.

---

## 💬 Bot Commands

| Command | Description |
|---------|-------------|
| `!translate <lang> <text>` | Translate text to the target language |
| `!tr <lang> <text>` | Short alias for translate |
| `!help` | Show usage guide |

**Example:**
```
!tr zh Hello, how are you?
!translate ja Good morning everyone
```

---

## 🗂️ File Structure

```
/home/container/
├── app.py               # Main application
├── panel.html           # Web management panel UI
├── requirements.txt     # Python dependencies
└── .npm/
    └── sub.txt          # Persistent configuration file
```

---

## 🔒 Security Notes

- The admin panel is protected by a password — **change it after first login**
- The Discord Token is stored locally in `.npm/sub.txt` — keep your container secure
- Sessions expire after **1 hour** of inactivity

---

## 📄 License

MIT — free to use, modify, and deploy.
