import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ===================== НАСТРОЙКИ ИЗ .env =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID ролей из .env (через запятую), легко добавлять новые
ROLE_IDS = [
    int(r) for r in os.getenv("ROLE_IDS", "").split(",") if r.strip()
]
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

        # Создаём приватную ветку
        thread = await channel.create_thread(
            name=f"ветка-{user.display_name}",
            type=discord.ChannelType.private_thread,
            invitable=False,
        )

        # Добавляем автора в ветку
        await thread.add_user(user)

        # Добавляем участников с нужными ролями поштучно (без @role, чтобы ветка была реально приватной)
        added_members = []
        for role_id in ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                for member in role.members:
                    if member != user and member != bot.user:
                        await thread.add_user(member)
                        added_members.append(member.mention)

        members_text = ", ".join(added_members) if added_members else "персонал"

        # Отправляем сообщение в ветку БЕЗ упоминания роли (только юзеры)
        await thread.send(
            f"Ветка создана! {members_text} и {user.mention}, пишите здесь."
        )

        # Отвечаем пользователю (эфемерное сообщение, видит только он)
        await interaction.response.send_message(
            f"Приватная ветка **ветка-{user.display_name}** создана! Загляни туда.",
            ephemeral=True,
        )


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user} (ID: {bot.user.id})")
    # Регистрируем persistent view, чтобы кнопка работала после перезапуска
    bot.add_view(CreateThreadButton())
    # Синхронизируем slash-команды
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано {len(synced)} команд(а).")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")


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
