import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

# ===================== НАСТРОЙКИ ИЗ .env =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID ролей из .env (через запятую), легко добавлять новые
ROLE_IDS = [
    int(r) for r in os.getenv("ROLE_IDS", "").split(",") if r.strip()
]

# ID владельца — бот пишет ему в ЛС при разархивации веток
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ID сервера — бот работает только на этом сервере
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
GUILD_OBJ = discord.Object(id=GUILD_ID) if GUILD_ID else None
# =============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


class CreateThreadButton(discord.ui.View):
    """View с кнопкой для создания приватной ветки."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Создать приватную ветку",
        style=discord.ButtonStyle.blurple,
        custom_id="create_private_thread",
    )
    async def create_thread(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        # Создаём приватную ветку (auto_archive_duration=10080 — максимум 7 дней)
        thread = await channel.create_thread(
            name=f"ветка-{user.display_name}",
            type=discord.ChannelType.private_thread,
            invitable=False,
            auto_archive_duration=10080,
        )

        # Добавляем автора в ветку
        await thread.add_user(user)

        # Добавляем участников с нужными ролями поштучно (для приватности)
        role_mentions = []
        for role_id in ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                role_mentions.append(role.mention)
                for member in role.members:
                    if member != user and member != bot.user:
                        await thread.add_user(member)

        roles_text = ", ".join(role_mentions) if role_mentions else "персонал"

        # Отправляем сообщение с упоминанием @роли
        await thread.send(
            f"Ветка создана! Участники с ролью {roles_text} и {user.mention}, пишите здесь."
        )

        # Отвечаем пользователю (эфемерное сообщение, видит только он)
        await interaction.response.send_message(
            f"Приватная ветка **ветка-{user.display_name}** создана! Загляни туда.",
            ephemeral=True,
        )


async def notify_owner(message: str):
    """Отправляет сообщение владельцу в ЛС."""
    if not OWNER_ID:
        return
    try:
        owner = await bot.fetch_user(OWNER_ID)
        await owner.send(message)
    except Exception as e:
        print(f"Не удалось отправить ЛС владельцу: {e}")


async def unarchive_bot_threads():
    """Проверяет архивированные ветки бота на нашем сервере и разархивирует их."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    for channel in guild.text_channels:
        try:
            async for thread in channel.archived_threads(limit=None):
                if thread.owner_id == bot.user.id:
                    await thread.edit(archived=False)
                    print(f"Ветка «{thread.name}» разархивирована (была пропущена).")
                    await notify_owner(
                        f"⚠️ Ветка **{thread.name}** в #{channel.name} пропала (заархивировалась), "
                        f"но я её восстановил."
                    )
        except discord.Forbidden:
            pass


@tasks.loop(minutes=5)
async def check_archived_threads():
    """Каждые 5 минут проверяет и разархивирует ветки бота."""
    await unarchive_bot_threads()


@check_archived_threads.before_loop
async def before_check():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user} (ID: {bot.user.id})")
    # Регистрируем persistent view, чтобы кнопка работала после перезапуска
    bot.add_view(CreateThreadButton())
    # Разархивируем ветки, которые могли заархивироваться пока бот был оффлайн
    await unarchive_bot_threads()
    # Запускаем фоновую проверку каждые 5 минут
    if not check_archived_threads.is_running():
        check_archived_threads.start()
    # Синхронизируем slash-команды только для нашего сервера
    try:
        bot.tree.copy_global_to(guild=GUILD_OBJ)
        synced = await bot.tree.sync(guild=GUILD_OBJ)
        print(f"Синхронизировано {len(synced)} команд(а) для сервера.")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")


@bot.event
async def on_thread_update(before, after):
    """Если ветка, созданная ботом, была заархивирована — разархивируем её."""
    if (
        after.archived
        and not before.archived
        and after.owner_id == bot.user.id
        and after.guild.id == GUILD_ID
        and isinstance(after, discord.Thread)
    ):
        try:
            await after.edit(archived=False)
            print(f"Ветка «{after.name}» разархивирована автоматически.")
            await notify_owner(
                f"⚠️ Ветка **{after.name}** в #{after.parent.name} пропала (заархивировалась), "
                f"но я её восстановил."
            )
        except Exception as e:
            print(f"Не удалось разархивировать ветку «{after.name}»: {e}")


@bot.tree.command(name="setup", description="Отправить сообщение с кнопкой для создания приватной ветки")
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Приватные ветки",
        description="Нажмите на кнопку ниже, чтобы создать приватную ветку.\n"
                    "В неё будут добавлены участники с нужной ролью.",
        color=discord.Color.blurple(),
    )
    await interaction.response.send_message(embed=embed, view=CreateThreadButton())


bot.run(BOT_TOKEN)
