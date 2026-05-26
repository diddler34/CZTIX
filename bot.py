import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


TICKET_TYPES = {
    "denuncia": "Denunciar Jogador",
    "bug": "Reportar Bug",
    "seguro": "Resgatar Seguro de Veículo",
    "doacao": "Doação / CZP / VIP",
    "base": "Problema com Base",
    "outro": "Outro Suporte",
}


class TicketModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        super().__init__(title=f"Ticket - {TICKET_TYPES[ticket_type]}")
        self.ticket_type = ticket_type

        self.steam_id = discord.ui.TextInput(
            label="Steam ID",
            placeholder="Digite sua Steam64 ID com exatamente 17 números",
            required=True,
            min_length=17,
            max_length=17
        )

        self.nickname = discord.ui.TextInput(
            label="Nick dentro do jogo",
            placeholder="Exemplo: JoãoBR",
            required=True,
            max_length=40
        )

        self.description = discord.ui.TextInput(
            label="Explique o problema",
            placeholder="Descreva com detalhes o que aconteceu...",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )

        self.proof = discord.ui.TextInput(
            label="Provas / horário / localização",
            placeholder="Vídeo, print, horário, cidade, coordenada, nome do jogador...",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=800
        )

        self.agreement = discord.ui.TextInput(
            label="Confirmação obrigatória",
            placeholder="Digite CONCORDO para confirmar que suas informações são verdadeiras.",
            required=True,
            min_length=8,
            max_length=8
        )

        self.add_item(self.steam_id)
        self.add_item(self.nickname)
        self.add_item(self.description)
        self.add_item(self.proof)
        self.add_item(self.agreement)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.steam_id.value.isdigit() or len(self.steam_id.value) != 17:
            await interaction.response.send_message(
                "Erro: sua Steam ID precisa conter exatamente 17 números. Exemplo: 76561198000000000",
                ephemeral=True
            )
            return

        if self.agreement.value.upper() != "CONCORDO":
            await interaction.response.send_message(
                "Você precisa digitar CONCORDO na confirmação obrigatória para abrir o ticket.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        category = guild.get_channel(TICKET_CATEGORY_ID)

        if support_role is None:
            await interaction.response.send_message(
                "Erro: cargo da staff não encontrado. Verifique SUPPORT_ROLE_ID no .env.",
                ephemeral=True
            )
            return

        if category is None:
            await interaction.response.send_message(
                "Erro: categoria de tickets não encontrada. Verifique TICKET_CATEGORY_ID no .env.",
                ephemeral=True
            )
            return

        channel_name = f"ticket-{interaction.user.name}".lower().replace(" ", "-")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),
            support_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True
            )
        }

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket de {interaction.user} | Tipo: {TICKET_TYPES[self.ticket_type]}"
        )

        embed = discord.Embed(
            title="Novo Ticket - CarnageZ",
            description="A staff irá analisar seu caso em breve.",
            color=discord.Color.red()
        )

        embed.add_field(name="Tipo de suporte", value=TICKET_TYPES[self.ticket_type], inline=False)
        embed.add_field(name="Jogador", value=interaction.user.mention, inline=True)
        embed.add_field(name="Steam ID", value=self.steam_id.value, inline=True)
        embed.add_field(name="Nick in-game", value=self.nickname.value, inline=True)
        embed.add_field(name="Descrição", value=self.description.value, inline=False)
        embed.add_field(
            name="Provas / informações extras",
            value=self.proof.value or "Não informado",
            inline=False
        )
        embed.add_field(
            name="Declaração do jogador",
            value=(
                "O jogador confirmou estar ciente de que qualquer tentativa de enganar a administração, "
                "fraudar o servidor, mentir intencionalmente ou tentar obter loot, benefícios, seguro, VIP ou CZP "
                "de forma desonesta poderá resultar em banimento permanente do servidor."
            ),
            inline=False
        )

        embed.set_footer(text="CarnageZ • Sistema de Tickets")

        await ticket_channel.send(
            content=f"{interaction.user.mention} {support_role.mention}",
            embed=embed,
            view=TicketControlView()
        )

        await interaction.response.send_message(
            f"Seu ticket foi criado: {ticket_channel.mention}",
            ephemeral=True
        )


class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Denunciar Jogador",
                value="denuncia",
                description="Cheater, abuso, racismo, quebra de regra"
            ),
            discord.SelectOption(
                label="Reportar Bug",
                value="bug",
                description="Bug do servidor, item sumindo, problema técnico"
            ),
            discord.SelectOption(
                label="Resgatar Seguro de Veículo",
                value="seguro",
                description="Pedido de seguro de carro"
            ),
            discord.SelectOption(
                label="Doação / CZP / VIP",
                value="doacao",
                description="Ajuda com pagamento, VIP ou CZP"
            ),
            discord.SelectOption(
                label="Problema com Base",
                value="base",
                description="Base bugada, storage, construção ou raid"
            ),
            discord.SelectOption(
                label="Outro Suporte",
                value="outro",
                description="Qualquer outro assunto"
            ),
        ]

        super().__init__(
            placeholder="Escolha o tipo de suporte...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="carnagez_ticket_type_select"
        )

    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        await interaction.response.send_modal(TicketModal(ticket_type))


class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Assumir Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="carnagez_assign_ticket"
    )
    async def assign_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)

        if support_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Apenas membros da staff podem assumir tickets.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Atendimento Assumido",
            description=f"Admin {interaction.user.mention} foi designado para este caso e estará com você em breve.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.secondary,
        custom_id="carnagez_close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)

        if support_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Apenas membros da staff podem fechar tickets.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("Este ticket será fechado em 5 segundos...")
        await asyncio.sleep(5)

        await interaction.channel.delete(reason=f"Ticket fechado por {interaction.user}")


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())

    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


@bot.tree.command(
    name="setup_ticket",
    description="Cria o painel de tickets do CarnageZ",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_ticket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Suporte CarnageZ",
        description=(
            "Precisa de ajuda? Abra um ticket abaixo.\n\n"
            "**Escolha o tipo correto de atendimento:**\n"
            "• Denunciar jogador\n"
            "• Reportar bug\n"
            "• Resgatar seguro de veículo\n"
            "• Doação / CZP / VIP\n"
            "• Problema com base\n"
            "• Outro suporte\n\n"
            "Tenha em mãos sua **Steam ID**, **nick in-game** e provas se necessário.\n\n"
            "**Atenção:** informações falsas, tentativas de fraude ou pedidos desonestos "
            "podem resultar em punição permanente no servidor."
        ),
        color=discord.Color.red()
    )

    embed.set_footer(text="CarnageZ • desenvolvido por Mak3r")

    await interaction.channel.send(embed=embed, view=TicketOpenView())
    await interaction.response.send_message(
        "Painel de tickets criado com sucesso.",
        ephemeral=True
    )


bot.run(BOT_TOKEN)
