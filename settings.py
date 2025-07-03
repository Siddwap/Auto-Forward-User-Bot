import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import events
from angel_db import collection
from angel_db import settings_col, admin_col, extra_targets_col

load_dotenv()

# ================= Configuration =================
WOODCRAFT_URL = os.getenv("WOODCRAFT_URL")
NOOR_URL = os.getenv("NOOR_URL")
DEFAULT_ADMINS = [1958355347]  # Hardcoded admin ID as a list

# ================== Functions ====================
async def add_target_channel(chat_id):
    if not extra_targets_col.find_one({"chat_id": chat_id}):
        extra_targets_col.insert_one({"chat_id": chat_id})

async def remove_target_channel(chat_id):
    extra_targets_col.delete_one({"chat_id": chat_id})

async def get_all_target_channels():
    return [doc["chat_id"] for doc in extra_targets_col.find()]

def is_admin(user_id):
    try:
        user_id = int(user_id)
        return user_id in DEFAULT_ADMINS
    except:
        return False

def add_admin(user_id):
    # Since admin is hardcoded, this function will not add new admins
    print(f"Cannot add admin: Admin ID is hardcoded to {DEFAULT_ADMINS[0]}")

def remove_admin(user_id):
    # Since admin is hardcoded, this function will not remove admins
    print(f"Cannot remove admin: Admin ID is hardcoded to {DEFAULT_ADMINS[0]}")

# ============== Event Handlers ================
def setup_extra_handlers(woodcraft):
    @woodcraft.on(events.NewMessage(pattern=r'^/setdelay (\d+)$'))
    async def set_delay(event):
        if not is_admin(event.sender_id):
            return
        seconds = int(event.pattern_match.group(1))
        settings_col.update_one(
            {"key": "delay"},
            {"$set": {"value": seconds}},
            upsert=True
        )
        woodcraft.delay_seconds = seconds
        await event.reply(f"⏱️ Delay set: {seconds}s")

    @woodcraft.on(events.NewMessage(pattern=r'^/skip$'))
    async def skip_msg(event):
        if not is_admin(event.sender_id):
            return
        settings_col.update_one(
            {"key": "skip_next"},
            {"$set": {"value": True}},
            upsert=True
        )
        woodcraft.skip_next_message = True
        await event.reply("⏭️ The next message will be skipped")

    @woodcraft.on(events.NewMessage(pattern=r'^/resume$'))
    async def resume(event):
        if not is_admin(event.sender_id):
            return
        settings_col.update_one(
            {"key": "skip_next"},
            {"$set": {"value": False}},
            upsert=True
        )
        woodcraft.skip_next_message = False
        await event.reply("▶️ Forwarding is on")

    @woodcraft.on(events.NewMessage(pattern=r'^/woodcraft$'))
    async def woodcraft_handler(event):
        if not is_admin(event.sender_id):
            await event.reply("❌ Not allowed!")
            return

        caption = """
**🔧 All commands list 🌟**

```👉 Click to copy command```

/status `/status`  
```⚡ View bot status```

/setdelay [Sec] `/setdelay`
```⏱️ Set the delay time.```

/skip `/skip`  
```🛹 Skip to next message```

/resume `/resume`  
```🏹 Start forwarding```

/on `/on` 
```✅ Launch the bot```

/off `/off` 
```📴 Close the bot```

/addtarget [ID] `/addtarget`  
```✅ Add target```

/removetarget [ID] `/removetarget` 
```😡 Remove target```

/listtargets `/listtargets` 
```🆔 View Target ID```

/addadmin `/addadmin` 
```➕ Promote a user to admin (non-permanent).```

/removeadmin `/removeadmin`
```➖ Remove a user from admin who was added using /addadmin.```

/listadmins `/listadmins`
```📋 View the list of all current admins.```

/noor `/noor`
```👀 Shows a detailed status report including:```

/count `/count`
```📊 Total Forwarded Files```

/restart `/restart`
```♻️ Restarts the bot safely.```

🖤⃝💔 𝐖𝐎𝐎𝐃𝐜𝐫𝐚𝐟𝐭 🖤⃝💔
"""

        await woodcraft.send_file(
            event.chat_id,
            file=WOODCRAFT_URL,
            caption=caption,
            parse_mode='md'
        )

    @woodcraft.on(events.NewMessage(pattern=r'^/addadmin$'))
    async def handle_add_admin(event):
        if not is_admin(event.sender_id):
            return await event.reply("❌ You are not an admin.")
        await event.reply(f"❌ Cannot add admin: Admin ID is hardcoded to {DEFAULT_ADMINS[0]}")

    @woodcraft.on(events.NewMessage(pattern=r'^/removeadmin$'))
    async def handle_remove_admin(event):
        if not is_admin(event.sender_id):
            return await event.reply("❌ You are not an admin.")
        await event.reply(f"❌ Cannot remove admin: Admin ID is hardcoded to {DEFAULT_ADMINS[0]}")

    @woodcraft.on(events.NewMessage(pattern=r'^/listadmins$'))
    async def list_admins(event):
        if not is_admin(event.sender_id):
            return await event.reply("❌ You are not an admin.")
        await event.reply(f"**👮 Admin List:**\n\n`{DEFAULT_ADMINS[0]}`", parse_mode='md')

    @woodcraft.on(events.NewMessage(pattern=r'^/restart$'))
    async def restart_bot(event):
        if not is_admin(event.sender_id):
            return await event.reply("❌ You are not an admin.")
        await event.reply("♻️ Successfully restarting bot ✅")
        await asyncio.sleep(2)
        sys.exit(0)

    @woodcraft.on(events.NewMessage(pattern=r'^/noor$'))
    async def noor_handler(event):
        if not is_admin(event.sender_id):
            await event.reply("❌ You are not an admin.")
            return

        targets = [str(doc["chat_id"]) for doc in extra_targets_col.find()]

        delay_data = settings_col.find_one({"key": "delay"})
        delay = delay_data["value"] if delay_data else 5

        skip_data = settings_col.find_one({"key": "skip_next"})
        skip_next = skip_data["value"] if skip_data else False

        current_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

        message = (
            "📦 **Bot status**\n\n"
            f"👑 **Admin (1):**\n`{DEFAULT_ADMINS[0]}`\n\n"
            f"🎯 **Target Channel ({len(targets)}):**\n`{', '.join(targets)}`\n\n"
            f"⏱️ **Delay:** `{delay} Sec`\n"
            f"⏭️ **Skip to next message:** `{skip_next}`\n\n"
            f"🕒 **Last backup:** `{current_time}`\n\n"
            f"⫷〇❖◉◉◉ 𝐖𝐎𝐎𝐃𝐜𝐫𝐚𝐟𝐭 ◉◉◉❖〇⫸"
        )

        try:
            await woodcraft.send_file(
                entity=event.chat_id,
                file=NOOR_URL,
                caption=message,
                parse_mode='md',
                force_document=False
            )
        except Exception as e:
            await event.reply(f"Error: {e}")

# ============ Initial Settings Loader ============
async def load_initial_settings(woodcraft):
    delay = settings_col.find_one({"key": "delay"})
    woodcraft.delay_seconds = delay["value"] if delay else 5

    skip_next = settings_col.find_one({"key": "skip_next"})
    woodcraft.skip_next_message = skip_next["value"] if skip_next else False
