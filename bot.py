import asyncio
import logging
from urllib.parse import quote

from pyrogram import Client, errors, filters
from pyrogram.errors import FloodWait
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from configs import cfg
from database import add_group, add_user, all_groups, all_users, remove_user, users

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Client ───────────────────────────────────────────────────────────────────
app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN,
)

# ── Reusable keyboards ────────────────────────────────────────────────────────
MAIN_KEYBOARD = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("🗯 Channel", url="https://t.me/vj_botz"),
        InlineKeyboardButton("💬 Support", url="https://t.me/vj_bot_disscussion"),
    ]]
)

START_CAPTION = (
    "**🦊 Hello {mention}!\n"
    "I'm an auto approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
    "I can approve users in Groups/Channels. Add me to your chat and promote me to admin "
    "with add members permission.\n\n__Powered By : @VJ_Botz __**"
)

START_PHOTO = "https://graph.org/file/d57d6f83abb6b8d0efb02.jpg"

# ── Helpers ───────────────────────────────────────────────────────────────────
async def is_subscribed(user_id: int) -> bool:
    """Return True if user is a member of the required channel."""
    try:
        await app.get_chat_member(cfg.CHID, user_id)
        return True
    except Exception:
        return False


async def get_force_join_keyboard() -> InlineKeyboardMarkup | None:
    """Build the force-join keyboard, or return None if invite link can't be created."""
    try:
        link = await app.create_chat_invite_link(int(cfg.CHID))
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🍿 Join Update Channel 🍿", url=link.invite_link),
            InlineKeyboardButton("🍀 Check Again 🍀", callback_data="chk"),
        ]])
    except Exception:
        return None


async def broadcast_message(m: Message, forward: bool = False) -> tuple[int, int, int, int]:
    """
    Broadcast a message to all users.

    Args:
        m: The /bcast or /fcast command message (reply_to_message is the content).
        forward: If True, forward instead of copy.

    Returns:
        (success, failed, deactivated, blocked) counts.
    """
    success = failed = deactivated = blocked = 0
    content = m.reply_to_message

    for doc in users.find({}, {"user_id": 1}):
        uid = int(doc["user_id"])
        try:
            if forward:
                await content.forward(uid)
            else:
                await content.copy(uid)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            try:
                if forward:
                    await content.forward(uid)
                else:
                    await content.copy(uid)
                success += 1
            except Exception:
                failed += 1
        except errors.InputUserDeactivated:
            deactivated += 1
            remove_user(uid)
        except errors.UserIsBlocked:
            blocked += 1
        except Exception as e:
            log.warning("Broadcast error for %s: %s", uid, e)
            failed += 1

    return success, failed, deactivated, blocked


# ── Handlers ──────────────────────────────────────────────────────────────────

# ── Auto-approve join requests ────────────────────────────────────────────────
@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m: Message):
    chat = m.chat
    user = m.from_user

    try:
        add_group(chat.id)
        await app.approve_chat_join_request(chat.id, user.id)
        add_user(user.id)
    except Exception as e:
        log.error("Failed to approve %s in %s: %s", user.id, chat.id, e)
        return

    # Build welcome DM
    try:
        chat_info = await app.get_chat(chat.id)
        invite = await app.create_chat_invite_link(chat.id)

        share_text = f"Join {chat_info.title}"
        if chat_info.description:
            share_text += f"\n\n{chat_info.description}"

        share_url = (
            f"https://t.me/share/url?"
            f"url={quote(invite.invite_link)}&text={quote(share_text)}"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔸 Share To Approve 🔸", url=share_url)],
            [
                InlineKeyboardButton("𝗡𝗮𝘃𝗮𝗿𝗲𝘀𝗮", url="https://t.me/+KUHDIO9bOTNjZDk1"),
                InlineKeyboardButton("𝗕𝗼𝗼𝗺𝗲𝘅 Channel", url="https://t.me/+WhVDuMbBIgYwMzQ1"),
            ],
            [InlineKeyboardButton("𝗕𝗼𝗼𝗺𝗲𝘅 Bot", url="https://t.me/Sofiya_tmtbot?start=start")],
        ])

        await app.send_message(
            user.id,
            f"**✅ You have been accepted to {chat.title}!**\n\n"
            f"Share this group with your friends to help us grow 🚀",
            reply_markup=keyboard,
        )
    except errors.PeerIdInvalid:
        log.info("User %s hasn't started the bot; skipping DM.", user.id)
    except Exception as e:
        log.warning("DM error for %s: %s", user.id, e)


# ── /start ────────────────────────────────────────────────────────────────────
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    if not await is_subscribed(m.from_user.id):
        keyboard = await get_force_join_keyboard()
        if keyboard is None:
            await m.reply("**Make Sure I Am Admin In Your Channel**")
            return
        await m.reply_text(
            "**⚠️ Access Denied! ⚠️\n\n"
            "Please join my Update Channel to use me. "
            "Once joined, tap **Check Again** to confirm.**",
            reply_markup=keyboard,
        )
        return

    add_user(m.from_user.id)
    await m.reply_photo(
        START_PHOTO,
        caption=START_CAPTION.format(mention=m.from_user.mention),
        reply_markup=MAIN_KEYBOARD,
    )


# ── Check-subscription callback ───────────────────────────────────────────────
@app.on_callback_query(filters.regex("^chk$"))
async def chk(_, cb: CallbackQuery):
    if not await is_subscribed(cb.from_user.id):
        await cb.answer(
            "🙅 You haven't joined the channel yet. Join first, then tap Check Again.",
            show_alert=True,
        )
        return

    add_user(cb.from_user.id)
    await cb.edit_message_text(
        text=START_CAPTION.format(mention=cb.from_user.mention),
        reply_markup=MAIN_KEYBOARD,
    )


# ── /users (sudo only) ────────────────────────────────────────────────────────
@app.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def db_stats(_, m: Message):
    u = all_users()
    g = all_groups()
    await m.reply_text(
        f"**🍀 Chat Stats 🍀**\n"
        f"🙋 Users : `{u}`\n"
        f"👥 Groups : `{g}`\n"
        f"🚧 Total : `{u + g}`"
    )


# ── /bcast (sudo only) ────────────────────────────────────────────────────────
@app.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def bcast(_, m: Message):
    if not m.reply_to_message:
        await m.reply("**Reply to a message to broadcast it.**")
        return

    status = await m.reply_text("`⚡ Broadcasting…`")
    s, f, d, b = await broadcast_message(m, forward=False)
    await status.edit(
        f"✅ Sent : `{s}`\n❌ Failed : `{f}`\n"
        f"👾 Blocked : `{b}`\n👻 Deactivated : `{d}`"
    )


# ── /fcast (sudo only) ────────────────────────────────────────────────────────
@app.on_message(filters.command("fcast") & filters.user(cfg.SUDO))
async def fcast(_, m: Message):
    if not m.reply_to_message:
        await m.reply("**Reply to a message to forward it.**")
        return

    status = await m.reply_text("`⚡ Forwarding…`")
    s, f, d, b = await broadcast_message(m, forward=True)
    await status.edit(
        f"✅ Sent : `{s}`\n❌ Failed : `{f}`\n"
        f"👾 Blocked : `{b}`\n👻 Deactivated : `{d}`"
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Bot is starting…")
    app.run()
