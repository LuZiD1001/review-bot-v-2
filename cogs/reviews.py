import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
CUSTOMER_ROLE_NAME  = "Customer"          # Rolle die Reviews schreiben darf
REVIEW_CHANNEL_NAME = "🎉│review"           # Channel wo Reviews gepostet werden
DATA_FILE           = "data/reviews.json" # Review-Datenbank

CATEGORIES = {
    "nve":      "🎨 NVE Preset",
    "settings": "⚙️ Settings / Tweaker",
    "custom":   "💎 Custom Paket",
}

STARS = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}

STAR_COLORS = {
    1: 0xFF4444,
    2: 0xFF8844,
    3: 0xFFCC00,
    4: 0x88DD00,
    5: 0x00CC66,
}

# ── Helper ────────────────────────────────────────────────────────────────────
def load_reviews() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reviews(reviews: list):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

# ── Modal ─────────────────────────────────────────────────────────────────────
class ReviewModal(discord.ui.Modal):
    def __init__(self, category: str, rating: int, screenshot_url: str | None):
        super().__init__(title=f"Review — {CATEGORIES[category]}")
        self.category      = category
        self.rating        = rating
        self.screenshot_url = screenshot_url

        self.review_text = discord.ui.TextInput(
            label="Dein Review",
            style=discord.TextStyle.paragraph,
            placeholder="Schreib hier deine Erfahrung...",
            min_length=10,
            max_length=500,
        )
        self.add_item(self.review_text)

    async def on_submit(self, interaction: discord.Interaction):
        reviews = load_reviews()

        entry = {
            "user_id":   interaction.user.id,
            "username":  str(interaction.user),
            "category":  self.category,
            "rating":    self.rating,
            "text":      self.review_text.value,
            "screenshot": self.screenshot_url,
            "timestamp": datetime.utcnow().isoformat(),
        }
        reviews.append(entry)
        save_reviews(reviews)

        # Review-Channel suchen
        channel = discord.utils.get(interaction.guild.text_channels, name=REVIEW_CHANNEL_NAME)
        if not channel:
            await interaction.response.send_message(
                f"❌ Channel `#{REVIEW_CHANNEL_NAME}` nicht gefunden! Bitte einen Admin informieren.",
                ephemeral=True
            )
            return

        # Embed bauen
        embed = discord.Embed(
            title=f"{STARS[self.rating]}  {CATEGORIES[self.category]}",
            description=f"*\"{self.review_text.value}\"*",
            color=STAR_COLORS[self.rating],
            timestamp=datetime.utcnow(),
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        embed.add_field(name="Bewertung", value=STARS[self.rating], inline=True)
        embed.add_field(name="Kategorie", value=CATEGORIES[self.category], inline=True)
        embed.set_footer(text=f"Review #{len(reviews)}")

        if self.screenshot_url:
            embed.set_image(url=self.screenshot_url)

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Dein Review wurde erfolgreich gepostet! Danke fürs Feedback 🙏",
            ephemeral=True
        )


# ── Views ─────────────────────────────────────────────────────────────────────
class RatingView(discord.ui.View):
    """Sternebewertung auswählen"""
    def __init__(self, category: str, screenshot_url: str | None):
        super().__init__(timeout=120)
        self.category       = category
        self.screenshot_url = screenshot_url

        for i in range(1, 6):
            btn = discord.ui.Button(
                label=f"{i} {'⭐' * i}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"star_{i}",
                row=0 if i <= 3 else 1,
            )
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, stars: int):
        async def callback(interaction: discord.Interaction):
            modal = ReviewModal(self.category, stars, self.screenshot_url)
            await interaction.response.send_modal(modal)
        return callback


class CategoryView(discord.ui.View):
    """Kategorie auswählen"""
    def __init__(self, screenshot_url: str | None):
        super().__init__(timeout=120)
        self.screenshot_url = screenshot_url

    @discord.ui.button(label="🎨 NVE Preset",       style=discord.ButtonStyle.primary,   row=0)
    async def nve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="**Schritt 2/3 — Wie viele Sterne gibst du?**",
            view=RatingView("nve", self.screenshot_url)
        )

    @discord.ui.button(label="⚙️ Settings/Tweaker", style=discord.ButtonStyle.primary,   row=0)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="**Schritt 2/3 — Wie viele Sterne gibst du?**",
            view=RatingView("settings", self.screenshot_url)
        )

    @discord.ui.button(label="💎 Custom Paket",     style=discord.ButtonStyle.primary,   row=0)
    async def custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="**Schritt 2/3 — Wie viele Sterne gibst du?**",
            view=RatingView("custom", self.screenshot_url)
        )


# ── Cog ───────────────────────────────────────────────────────────────────────
class Reviews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def has_customer_role(self, member: discord.Member) -> bool:
        return any(r.name == CUSTOMER_ROLE_NAME for r in member.roles)

    # /review [screenshot]
    @app_commands.command(name="review", description="Schreib ein Review für dein gekauftes Produkt")
    @app_commands.describe(screenshot="Optional: Screenshot von deinem Grafik-Setup")
    async def review(
        self,
        interaction: discord.Interaction,
        screenshot: discord.Attachment | None = None,
    ):
        if not self.has_customer_role(interaction.user):
            await interaction.response.send_message(
                f"❌ Du benötigst die **{CUSTOMER_ROLE_NAME}**-Rolle um ein Review zu schreiben.",
                ephemeral=True
            )
            return

        screenshot_url = screenshot.url if screenshot else None

        await interaction.response.send_message(
            "**Schritt 1/3 — Was möchtest du bewerten?**",
            view=CategoryView(screenshot_url),
            ephemeral=True
        )

    # /reviews-stats
    @app_commands.command(name="review-stats", description="Zeigt die Review-Statistiken")
    async def review_stats(self, interaction: discord.Interaction):
        reviews = load_reviews()
        if not reviews:
            await interaction.response.send_message("📭 Noch keine Reviews vorhanden.", ephemeral=True)
            return

        total  = len(reviews)
        avg    = sum(r["rating"] for r in reviews) / total
        counts = {k: 0 for k in CATEGORIES}
        for r in reviews:
            counts[r["category"]] = counts.get(r["category"], 0) + 1

        embed = discord.Embed(
            title="📊 Review Statistiken",
            color=0x5865F2,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Reviews gesamt", value=f"`{total}`",               inline=True)
        embed.add_field(name="Ø Bewertung",    value=f"`{avg:.1f} ⭐`",          inline=True)
        embed.add_field(name="\u200b",         value="\u200b",                    inline=True)

        for key, label in CATEGORIES.items():
            cat_reviews = [r for r in reviews if r["category"] == key]
            if cat_reviews:
                cat_avg = sum(r["rating"] for r in cat_reviews) / len(cat_reviews)
                embed.add_field(
                    name=label,
                    value=f"{len(cat_reviews)} Reviews • Ø {cat_avg:.1f} ⭐",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reviews(bot))
