import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import time
from discord import Embed
import yt_dlp
import asyncio



intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

game_data = {}
word_game_data = {}
current_number = 0

# JSON dosyaları
DATA_FILE = "bom_game_channels.json"
WORD_GAME_FILE = "word_game_channels.json"
STATUS_FILE = "game_status.json"  # Kanal durum dosyası

def load_data():
    global game_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            game_data = json.load(f)
    else:
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(game_data, f)

def load_word_game_data():
    global word_game_data
    if os.path.exists(WORD_GAME_FILE):
        with open(WORD_GAME_FILE, "r") as f:
            word_game_data = json.load(f)
    else:
        with open(WORD_GAME_FILE, "w") as f:
            json.dump({}, f)

def save_word_game_data():
    with open(WORD_GAME_FILE, "w") as f:
        json.dump(word_game_data, f)

def load_status():
    global status_data
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            status_data = json.load(f)
    else:
        with open(STATUS_FILE, "w") as f:
            json.dump({}, f)

def save_status():
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f)

start_time = datetime.now()  # Botun başladığı zaman

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı!')
    load_data()
    load_word_game_data()
    load_status()
    await bot.change_presence(activity=discord.Game(name="İsmetin Kalbi İle"))
    status_update.start()  # Durum güncelleme görevini başlat

@bot.command(name="bomoyunu")
@commands.has_permissions(administrator=True)
async def start_bom(ctx):
    global current_number
    channel_id = str(ctx.channel.id)
    load_status()  # Durumu kontrol et

    if channel_id in word_game_data and word_game_data[channel_id]["paused"]:
        await ctx.send("Bu kanalda aktif bir kelime oyunu var. Lütfen önce kelime oyununu durdurun.")
        return

    if channel_id in status_data and status_data[channel_id] == "active":
        await ctx.send("Bu kanalda zaten aktif bir bom oyunu var.")
        return

    if channel_id not in game_data:
        game_data[channel_id] = {
            "current_number": 0,
            "scores": {},
            "paused": False
        }
        status_data[channel_id] = "active"  # Durumu aktif olarak işaretle
        save_data()
        save_status()
        await ctx.send("Bom oyunu bu kanalda başladı! Her bir doğru sayınızda 5 puan ve her bir doğru 'bom' mesajınızda 10 puan kazanırsınız! Oyun skorlarını öğrenmek için !skor yazabilirsiniz. Eğer odada oyun dışında bir mesaj atmak isterseniz mesajınızın başına . koymalısınız. Örnek: .mesaj . mesaj")
    else:
        if game_data[channel_id]["paused"]:
            game_data[channel_id]["paused"] = False
            status_data[channel_id] = "active"  # Durumu aktif olarak işaretle
            save_data()
            save_status()
            await ctx.send("Bom oyunu tekrar başladı!")
        else:
            await ctx.send("Bu kanalda zaten bom oyunu oynanıyor.")

@bot.command(name="bomoyunudurdur")
@commands.has_permissions(administrator=True)
async def stop_bom(ctx):
    channel_id = str(ctx.channel.id)
    if channel_id in game_data:
        game_data[channel_id]["paused"] = True
        status_data[channel_id] = "disabled"  # Durumu devre dışı olarak işaretle
        save_data()
        save_status()
        await ctx.send("Bom oyunu bu kanalda durduruldu. Oyun tekrar başlatıldığında kaldığı yerden devam edecektir.")
    else:
        await ctx.send("Bu kanalda aktif bir bom oyunu yok.")

@bot.command(name="kelimeoyunu")
@commands.has_permissions(administrator=True)
async def start_word_game(ctx):
    channel_id = str(ctx.channel.id)
    load_status()  # Durumu kontrol et

    if channel_id in status_data and status_data[channel_id] == "active":
        await ctx.send("Bu kanalda aktif bir bom oyunu var. Lütfen önce bom oyununu durdurun.")
        return

    if channel_id in word_game_data:
        if word_game_data[channel_id]["paused"]:
            word_game_data[channel_id]["paused"] = False
            status_data[channel_id] = "active"  # Durumu aktif olarak işaretle
            save_word_game_data()
            save_status()
            await ctx.send("Kelime oyunu tekrar başladı!")
        else:
            await ctx.send("Bu kanalda zaten kelime oyunu oynanıyor.")
    else:
        word_game_data[channel_id] = {
            "last_word": None,
            "paused": False,
            "used_words": {},
            "scores": {}
        }
        status_data[channel_id] = "active"  # Durumu aktif olarak işaretle
        save_word_game_data()
        save_status()
        await ctx.send("Kelime oyunu bu kanalda başladı! Her yeni kelime, önceki kelimenin son harfi ile başlamalıdır. Her doğru kelime için 5 puan kazanırsınız. Oyun duraklatmak için !kelimeoyunudurdur yazabilirsiniz.")

@bot.command(name="kelimeoyunudurdur")
@commands.has_permissions(administrator=True)
async def stop_word_game(ctx):
    channel_id = str(ctx.channel.id)
    if channel_id in word_game_data:
        word_game_data[channel_id]["paused"] = True
        status_data[channel_id] = "disabled"  # Durumu devre dışı olarak işaretle
        save_word_game_data()
        save_status()
        await ctx.send("Kelime oyunu bu kanalda durduruldu. Oyun tekrar başlatıldığında kaldığı yerden devam edecektir.")
    else:
        await ctx.send("Bu kanalda aktif bir kelime oyunu yok.")

@bot.command(name="bomoyunureset")
@commands.has_permissions(administrator=True)
async def reset_bom(ctx):
    channel_id = str(ctx.channel.id)
    if channel_id in game_data:
        # Oyuncu verilerini sıfırla
        del game_data[channel_id]
        # Durumu da sıfırla
        if channel_id in status_data:
            del status_data[channel_id]
        save_data()
        save_status()
        await ctx.send("Bom oyunu verileri sıfırlandı. Oyun tekrar başlatabilirsiniz.")
    else:
        await ctx.send("Bu kanalda aktif bir bom oyunu bulunmuyor.")

@bot.command(name="kelimeoyunureset")
@commands.has_permissions(administrator=True)
async def reset_word_game(ctx):
    channel_id = str(ctx.channel.id)
    if channel_id in word_game_data:
        # Oyuncu verilerini sıfırla
        del word_game_data[channel_id]
        # Durumu da sıfırla
        if channel_id in status_data:
            del status_data[channel_id]
        save_word_game_data()
        save_status()
        await ctx.send("Kelime oyunu verileri sıfırlandı. Oyun tekrar başlatabilirsiniz.")
    else:
        await ctx.send("Bu kanalda aktif bir kelime oyunu bulunmuyor.")



        

@bot.command(name="skor")
async def skor(ctx):
    channel_id = str(ctx.channel.id)

    # Bom oyunu skorlarını kontrol et ve sırala
    bom_scores = game_data.get(channel_id, {}).get("scores", {})
    bom_score_embed = Embed(title="Bom Oyunu Skorları", color=0x00ff00)  # Yeşil renk
    bom_has_scores = False
    if bom_scores:
        sorted_bom_scores = sorted(bom_scores.items(), key=lambda x: x[1], reverse=True)
        for user_id, score in sorted_bom_scores:
            user = await bot.fetch_user(int(user_id))
            bom_score_embed.add_field(name=user.name, value=f"{score} puan", inline=False)
        bom_has_scores = True

    # Kelime oyunu skorlarını kontrol et ve sırala
    kelime_scores = word_game_data.get(channel_id, {}).get("scores", {})
    kelime_score_embed = Embed(title="Kelime Oyunu Skorları", color=0xff0000)  # Kırmızı renk
    kelime_has_scores = False
    if kelime_scores:
        sorted_kelime_scores = sorted(kelime_scores.items(), key=lambda x: x[1], reverse=True)
        for user_id, score in sorted_kelime_scores:
            user = await bot.fetch_user(int(user_id))
            kelime_score_embed.add_field(name=user.name, value=f"{score} puan", inline=False)
        kelime_has_scores = True

    # Skorları kanala gönder
    if bom_has_scores:
        await ctx.send(embed=bom_score_embed)
    if kelime_has_scores:
        await ctx.send(embed=kelime_score_embed)
    if not bom_has_scores and not kelime_has_scores:
        await ctx.send("Bu kanalda aktif bir bom veya kelime oyunu bulunmuyor.")


@bot.command(name="toplamskor")
async def toplam_skor(ctx):
    # Kullanıcının toplam puanlarını hesaplamak için bir sözlük oluştur
    toplam_puanlar = {}

    # Bom oyunu verilerini yükle
    load_data()

    # Kelime oyunu verilerini yükle
    load_word_game_data()

    # Bom oyunu verilerini kontrol et
    for channel_id, data in game_data.items():
        scores = data.get("scores", {})
        for user_id, score in scores.items():
            toplam_puanlar[user_id] = toplam_puanlar.get(user_id, 0) + score

    # Kelime oyunu verilerini kontrol et
    for channel_id, data in word_game_data.items():
        scores = data.get("scores", {})
        for user_id, score in scores.items():
            toplam_puanlar[user_id] = toplam_puanlar.get(user_id, 0) + score

    # Sonuçları mesaj olarak oluştur
    if toplam_puanlar:
        sonuc_mesaji = "Toplam Skorlar:\n"
        sorted_puanlar = sorted(toplam_puanlar.items(), key=lambda x: x[1], reverse=True)
        for user_id, toplam_puan in sorted_puanlar:
            user = await bot.fetch_user(int(user_id))
            sonuc_mesaji += f"{user.name}: {toplam_puan} puan\n"
    else:
        sonuc_mesaji = "Bu sunucuda aktif bir oyun bulunmuyor."

    # Sonuç mesajını kanala gönder
    await ctx.send(sonuc_mesaji)













    



# Kelime dosyalarının yolu
WORDS_DIRECTORY = "kelimeler"  # 'kelimeler' klasörü kelime dosyalarını içermelidir

def kelime_gecerli_mi(kelime):
    # Kelimenin ilk harfini al ve küçük harfe dönüştür
    ilk_harf = kelime[0].lower()

    # Eğer ilk harf büyük İ'ye denk geliyorsa küçük i olarak değerlendir
    if ilk_harf == "i" and kelime[0] == "İ":
        dosya_harf = "i"
    # Eğer ilk harf büyük I'ye denk geliyorsa küçük ı olarak değerlendir
    elif ilk_harf == "i" and kelime[0] == "I":
        dosya_harf = "ı"
    else:
        dosya_harf = ilk_harf

    # Dosya yolunu oluştur
    dosya_yolu = os.path.join(WORDS_DIRECTORY, f"{dosya_harf}.txt")

    # Dosyayı kontrol et ve kelimeyi ara
    if os.path.exists(dosya_yolu):
        with open(dosya_yolu, "r", encoding="utf-8") as dosya:
            kelimeler = dosya.read().splitlines()
            return kelime.lower() in [k.lower() for k in kelimeler]
    return False

@bot.event
async def on_message(message):
    global current_number

    if message.author.bot:
        return

    channel_id = str(message.channel.id)

    # Kelime oyununu kontrol et
    if channel_id in word_game_data:
        if word_game_data[channel_id]["paused"]:
            await bot.process_commands(message)
            return

        if message.content.startswith("!"):
            await bot.process_commands(message)
            return

        # Mesajı küçük harfe çevir ve İ ve I harflerini doğru harflere dönüştür
        content = message.content.strip().lower()
        content = content.replace("ı", "ı").replace("i̇", "i").replace("i", "i")

        # Birden fazla kelime varsa çarpı emojisi ekleyip mesajı geç
        if len(content.split()) > 1:
            await message.add_reaction("❌")
            return

        # Noktayla başlayan mesajları iki kelimeli mesaj olarak değerlendir
        if content.startswith("."):
            await message.add_reaction("❌")
            return

        # Diğer kelime oyunu işlemleri
        last_word = word_game_data[channel_id].get("last_word", None)
        used_words = word_game_data[channel_id]["used_words"]
        scores = word_game_data[channel_id]["scores"]

        if last_word:
            if content in used_words:
                timestamp = used_words[content]["time"]
                author_id = used_words[content]["author"]
                author = await bot.fetch_user(int(author_id))
                await message.channel.send(f'{message.author.mention}, bu kelime daha önce yazıldı: "{content}". {timestamp} tarihinde {author.name} tarafından yazılmıştır.')
                try:
                    await message.delete()
                except discord.Forbidden:
                    await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
                return

            if content[0] != last_word[-1]:
                await message.channel.send(f'{message.author.mention}, kelime önceki kelimenin son harfiyle başlamalıdır.')
                try:
                    await message.delete()
                except discord.Forbidden:
                    await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
                return

            if not kelime_gecerli_mi(content):
                await message.channel.send(f'{message.author.mention}, yazdığınız kelime sözlükte bulunamadı.')
                try:
                    await message.delete()
                except discord.Forbidden:
                    await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
                return

        word_game_data[channel_id]["last_word"] = content
        used_words[content] = {
            "author": str(message.author.id),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        user_id = str(message.author.id)
        scores[user_id] = scores.get(user_id, 0) + 5
        
        # "ğ" ile biten kelime kontrolü
        if content.endswith("ğ"):
            scores[user_id] += 50
            await message.channel.send(f'{message.author.mention}, kelimenin sonu "ğ" ile bittiği için 50 puan kazandınız! Oyun sıfırlandı.')
            # Sadece son kelimeyi ve kullanılan kelimeleri sıfırla
            word_game_data[channel_id]["last_word"] = None
            word_game_data[channel_id]["used_words"] = {}
            save_word_game_data()
        else:
            save_word_game_data()
            await message.add_reaction("✅")
        return

    # Bom oyunu işlemleri
    if channel_id in game_data:
        if game_data[channel_id]["paused"]:
            await bot.process_commands(message)
            return

        current_number = game_data[channel_id].get("current_number", 0)

        if message.content.startswith("!"):
            await bot.process_commands(message)
            return

        if message.content.startswith("."):
            await message.add_reaction("🔖")
            return

        if message.content.lower() == "bom":
            if (current_number + 1) % 5 == 0:
                current_number += 1
                game_data[channel_id]["current_number"] = current_number

                user_id = str(message.author.id)
                game_data[channel_id]["scores"][user_id] = game_data[channel_id]["scores"].get(user_id, 0) + 10
                
                await message.add_reaction("💣")
                save_data()
            else:
                try:
                    await message.delete()
                except discord.Forbidden:
                    await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
                await message.channel.send(f'{message.author.mention}, "bom" yazmak için 5\'in katı olan bir sayıya gelmelisiniz.', delete_after=5)
            return

        try:
            guess = int(message.content)
            if guess == current_number + 1:
                current_number += 1
                if current_number % 5 == 0:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
                    await message.channel.send(f'{message.author.mention}, 5\'in katı geldiğinde "bom" yazmanız gerekiyor!', delete_after=5)
                    return
                else:
                    game_data[channel_id]["current_number"] = current_number

                    user_id = str(message.author.id)
                    game_data[channel_id]["scores"][user_id] = game_data[channel_id]["scores"].get(user_id, 0) + 5
                    
                    await message.add_reaction("✅")
                    save_data()
            else:
                try:
                    await message.delete()
                except discord.Forbidden:
                    await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
                await message.channel.send(f'{message.author.mention}, geçerli bir sayı girmelisiniz! Sonraki sayı {current_number + 1} olmalı.', delete_after=5)
            return

        except ValueError:
            try:
                await message.delete()
            except discord.Forbidden:
                await message.channel.send(f'{message.author.mention}, mesajınızı silemedim. Yeterli iznim yok.', delete_after=5)
            await message.channel.send(f'{message.author.mention}, yanlış mesaj! Sadece sayı veya "bom" yazabilirsiniz.', delete_after=5)
            return

    await bot.process_commands(message)



    


    

status_index = 0  # Durumlar arasında geçiş yapacak indeks

@tasks.loop(seconds=10)
async def status_update():
    global status_index
    toplam_kullanici = sum(guild.member_count for guild in bot.guilds)
    toplam_sunucu = len(bot.guilds)
    
    statuses = [
        f"Bot açık: {format_timedelta(datetime.now() - start_time)}",
        f"Toplam Kullanıcı: {toplam_kullanici}",
        f"Toplam Sunucu: {toplam_sunucu}",
        "Sürüm v0.5.5",
        "Made by Gökhan Özen",
        "!yardım",
        "Anderson Hosting güvencesiyle!",
        "Bom Oyunu",
        "Kelime Oyunu",
        "!skor ile puanlarınızı görün!",
    ]
    current_status = statuses[status_index]
    await bot.change_presence(activity=discord.Game(name=current_status))
    status_index = (status_index + 1) % len(statuses)  # İndeksi döngüye al



def format_timedelta(td):
    """Verilen timedelta objesini gün/saat/dakika/saniye formatında döndürür."""
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}g {hours}s {minutes}d {seconds}s"

@bot.command(name="yardım")
async def yardım(ctx):
    # Toplam kullanıcı ve toplam sunucu sayısını hesapla
    toplam_kullanici = sum(guild.member_count for guild in bot.guilds)
    toplam_sunucu = len(bot.guilds)
    
    uptime = format_timedelta(datetime.now() - start_time)

    embed = Embed(
        title="Yardım Menüsü",
        description="Botun sunduğu komutlar ve oyunlar hakkında detaylı bilgi.",
        color=0x3498db  # Mavi renk
    )

    embed.add_field(
        name="**Bom Oyunu**",
        value=(
            "**!bomoyunu** - Bom oyununu başlatır veya devam ettirir.\n"
            "**!bomoyunudurdur** - Bom oyununu durdurur.\n"
            "**!bomoyunureset** - Bom oyunu verilerini sıfırlar ve yeniden başlatır.\n\n"
            "**Bom Oyunu Talimatları:**\n"
            "1. Oyun başladığında sırasıyla numaralar yazılır.\n"
            "2. 5'in katı olan sayılar yerine 'bom' yazılmalıdır.\n"
            "3. Doğru yazılmış numaralar veya 'bom' ile ilerleyin."
        ),
        inline=False
    )
    
    embed.add_field(
        name="**Kelime Oyunu**",
        value=(
            "**!kelimeoyunu** - Kelime oyununu başlatır veya devam ettirir.\n"
            "**!kelimeoyunudurdur** - Kelime oyununu durdurur.\n"
            "**!kelimeoyunureset** - Kelime oyunu verilerini sıfırlar ve yeniden başlatır.\n\n"
            "**Kelime Oyunu Talimatları:**\n"
            "1. İlk kelimeyi yazın.\n"
            "2. Her yeni kelime, önceki kelimenin son harfi ile başlamalıdır.\n"
            "3. Tekrar eden kelimeler veya kurallara uymayan kelimeler hata olarak kabul edilir."
        ),
        inline=False
    )

    embed.add_field(
        name="**Genel Komutlar**",
        value=(
            "**!skor** - Kanalda oynanan bom ve kelime oyunlarının skorlarını gösterir.\n"
            "**!toplamskor** - Sunucudaki toplam bom ve kelime oyunlarının skorlarını gösterir.\n"
            "**!ping** - Botun yanıt süresini gösterir.\n"
            "**!sunucular** - Botun bulunduğu sunucuları listeler ve bazı bilgileri gösterir.\n"
            "**!sunucubilgi** - Kullanıldığı sunucu hakkında detaylı bilgi verir.\n"
            "**!davet** - Botu sunucunuza davet etmek için gerekli bağlantıyı sağlar."
        ),
        inline=False
    )
    
    embed.add_field(
        name="**Diğer**",
        value=(
            "**!yardım** - Bu yardım mesajını gösterir."
        ),
        inline=False
    )
    
    embed.set_footer(
        text=f"Botun çalışma süresi: {uptime}\n"
             f"Toplam Kullanıcı Sayısı: {toplam_kullanici}\n"
             f"Toplam Sunucu Sayısı: {toplam_sunucu}\n"
             f"Kurucu: <@427159467352915970>"
    )

    await ctx.send(embed=embed)

@bot.command(name="oyunlar")
async def yardım(ctx):
    # Toplam kullanıcı ve toplam sunucu sayısını hesapla
    toplam_kullanici = sum(guild.member_count for guild in bot.guilds)
    toplam_sunucu = len(bot.guilds)
    
    uptime = format_timedelta(datetime.now() - start_time)

    embed = Embed(
        title="Oyun Menüsü",
        description="Botun sunduğu komutlar ve oyunlar hakkında detaylı bilgi.",
        color=0x3498db  # Mavi renk
    )

    embed.add_field(
        name="**Bom Oyunu**",
        value=(
            "**!bomoyunu** - Bom oyununu başlatır veya devam ettirir.\n"
            "**!bomoyunudurdur** - Bom oyununu durdurur.\n"
            "**!bomoyunureset** - Bom oyunu verilerini sıfırlar ve yeniden başlatır.\n\n"
            "**Bom Oyunu Talimatları:**\n"
            "1. Oyun başladığında sırasıyla numaralar yazılır.\n"
            "2. 5'in katı olan sayılar yerine 'bom' yazılmalıdır.\n"
            "3. Doğru yazılmış numaralar veya 'bom' ile ilerleyin."
        ),
        inline=False
    )
    
    embed.add_field(
        name="**Kelime Oyunu**",
        value=(
            "**!kelimeoyunu** - Kelime oyununu başlatır veya devam ettirir.\n"
            "**!kelimeoyunudurdur** - Kelime oyununu durdurur.\n"
            "**!kelimeoyunureset** - Kelime oyunu verilerini sıfırlar ve yeniden başlatır.\n\n"
            "**Kelime Oyunu Talimatları:**\n"
            "1. İlk kelimeyi yazın.\n"
            "2. Her yeni kelime, önceki kelimenin son harfi ile başlamalıdır.\n"
            "3. Tekrar eden kelimeler veya kurallara uymayan kelimeler hata olarak kabul edilir."
        ),
        inline=False
    )

    embed.add_field(
        name="**Genel Komutlar**",
        value=(
            "**!skor** - Kanalda oynanan bom ve kelime oyunlarının skorlarını gösterir.\n"
            "**!toplamskor** - Sunucudaki toplam bom ve kelime oyunlarının skorlarını gösterir.\n"
            "**!davet** - Botu sunucunuza davet etmek için gerekli bağlantıyı sağlar."
        ),
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx):
    # Botun yanıt süresini ölç
    start_time = time.time()
    message = await ctx.send("Ping...")
    end_time = time.time()

    # Botun yanıt süresi ve API ping değeri
    latency = bot.latency * 1000  # ms cinsinden
    response_time = (end_time - start_time) * 1000  # ms cinsinden
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Yanıt mesajı
    await message.edit(content=f"""
**Botun Yanıt Süresi:**
- Bot Yanıt Süresi: {latency:.2f} ms
- API Yanıt Süresi: {response_time:.2f} ms
- Güncel Zaman: {current_time}
- Sunucu Ping Değeri: {int(latency)} ms
""")

@bot.command(name="davet")
async def davet(ctx):
    invite_url = "https://discord.com/oauth2/authorize?client_id=1270747997411475456&scope=bot&permissions=8"
    await ctx.send(f"Botu sunucunuza davet etmek için [bu bağlantıyı](https://discord.com/oauth2/authorize?client_id=1270747997411475456&scope=bot&permissions=8) kullanabilirsiniz.")

def format_timedelta(td):
    """Verilen timedelta objesini gün/saat/dakika/saniye formatında döndürür."""
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}g {hours}s {minutes}d {seconds}s"


@bot.command()
async def sunucular(ctx):
    for guild in bot.guilds:
        embed = discord.Embed(title="Sunucu Bilgileri", color=discord.Color.blurple())
        
        # Sunucu sahibi
        owner = guild.owner
        if owner is not None:
            owner_info = f"{owner.name}#{owner.discriminator}"
        else:
            owner_info = "Bilinmiyor"
        
        # Sunucudaki bot sayısı
        bot_count = sum(1 for member in guild.members if member.bot)
        
        # Sunucudaki kanal sayısı
        channel_count = len(guild.channels)
        
        # Sunucunun davet linki (izinler yetersizse bir mesaj göster)
        try:
            invite_links = await guild.invites()
            if invite_links:
                invite_link = invite_links[0].url
            else:
                invite_link = "Davet linki bulunamadı"
        except discord.errors.Forbidden:
            invite_link = "İzinler yetersiz, davet linki alınamadı"
        
        # Sunucu fotoğrafını ekle
        if guild.icon:
            icon_url = guild.icon.url
            embed.set_thumbnail(url=icon_url)
        else:
            icon_url = None  # Sunucu fotoğrafı yoksa boş bırak
        
        # Sunucu bilgilerini embed alanına ekle
        embed.add_field(
            name=guild.name,
            value=(
                f"Sahibi: {owner_info}\n"
                f"Üye Sayısı: {guild.member_count}\n"
                f"Bot Sayısı: {bot_count}\n"
                f"Kanal Sayısı: {channel_count}\n"
                f"Davet Linki: {invite_link}"
            ),
            inline=False
        )
        
        # Her sunucu için ayrı embed mesajı gönder
        await ctx.send(embed=embed)


@bot.command()
async def sunucubilgi(ctx):
    guild = ctx.guild
    embed = discord.Embed(title="Sunucu İstatistikleri", color=discord.Color.blue())

    # Sunucu bilgileri
    embed.add_field(name="Sunucu Adı", value=guild.name, inline=False)
    embed.add_field(name="Sunucu ID", value=guild.id, inline=False)
    embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=False)
    
    # Bot sayısı
    bot_count = sum(1 for member in guild.members if member.bot)
    embed.add_field(name="Bot Sayısı", value=bot_count, inline=False)
    
    # Kanal sayısı
    channel_count = len(guild.channels)
    embed.add_field(name="Kanal Sayısı", value=channel_count, inline=False)
    
    # Rol sayısı
    role_count = len(guild.roles)
    embed.add_field(name="Rol Sayısı", value=role_count, inline=False)
    
    # Sunucu sahibi
    owner = guild.owner
    owner_info = f"{owner.name}#{owner.discriminator}" if owner else "Bilinmiyor"
    embed.add_field(name="Sunucu Sahibi", value=owner_info, inline=False)
    
    # Sunucunun oluşturulma tarihi
    created_at = guild.created_at.strftime("%d/%m/%Y %H:%M:%S")
    embed.add_field(name="Oluşturulma Tarihi", value=created_at, inline=False)
    
    # Sunucu fotoğrafı
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await ctx.send(embed=embed)


@bot.command(name="bomoyunubastan")
@commands.has_permissions(administrator=True)
async def reset_bom_start(ctx):
    channel_id = str(ctx.channel.id)
    if channel_id in game_data:
        # current_number değerini sıfırla
        game_data[channel_id]["current_number"] = 0
        save_data()
        await ctx.send("Bom oyunu başladığı yerden sıfırlandı!")
    else:
        await ctx.send("Bu kanalda aktif bir bom oyunu bulunmuyor.")

@bot.command(name="kelimeoyunubastan")
@commands.has_permissions(administrator=True)
async def reset_word_game_start(ctx):
    channel_id = str(ctx.channel.id)
    if channel_id in word_game_data:
        # last_word ve used_words değerlerini sıfırla
        word_game_data[channel_id]["last_word"] = None
        word_game_data[channel_id]["used_words"] = {}
        # Skorları koru
        save_word_game_data()
        await ctx.send("Kelime oyunu başladığı yerden sıfırlandı. Önceki kelimeler temizlendi fakat kullanıcı skorları korundu!")
    else:
        await ctx.send("Bu kanalda aktif bir kelime oyunu bulunmuyor.")



# YT-DLP ayarları
ydl_opts = {
    'format': 'best',
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',  # 'webp' yerine 'mp4' gibi bir format belirleyin
    }]
}


song_queue = []

@bot.command(name='oynat')
async def oynat(ctx, url: str):
    global song_queue
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("Bir ses kanalında olmalısınız!")
        return

    # Şarkıyı sıraya ekle
    song_queue.append(url)
    song_position = len(song_queue)  # Şarkının sıradaki pozisyonu

    if not ctx.voice_client:
        # Ses kanalına katıl
        voice_client = await voice_channel.connect()
    else:
        voice_client = ctx.voice_client

    if not voice_client.is_playing():
        await play_next_song(ctx)

    await ctx.send(f"Şarkı sıraya eklendi! Sıradaki pozisyonu: {song_position}")

async def play_next_song(ctx):
    global song_queue
    if len(song_queue) > 0:
        url = song_queue.pop(0)

        # Youtube videosunu indir
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webp", ".mp3")

        # Ses dosyasını oynat
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=filename), after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))

        # Şarkı adı
        song_title = info.get('title', 'Şarkı adı bulunamadı')
        await ctx.send(f"Şu anda oynatılan şarkı: {song_title}")

@bot.command(name='sıra')
async def sıra(ctx):
    global song_queue
    if len(song_queue) == 0:
        await ctx.send("Şarkı sırası boş!")
    else:
        queue_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(song_queue)])
        await ctx.send(f"Şarkı sırası:\n{queue_list}")

@bot.command(name='durdur')
async def durdur(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Müzik durduruldu.")
    else:
        await ctx.send("Şu anda oynatılan bir müzik yok.")

@bot.command(name="odaya_katil")
async def odaya_katil(ctx):
    if ctx.author.voice is None:
        await ctx.send("Bir ses kanalına bağlı olmanız gerekiyor.")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
        await ctx.send(f"{channel.name} kanalına katıldım.")
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)
        await ctx.send(f"{channel.name} kanalına geçiş yaptım.")
    else:
        await ctx.send("Zaten bu ses kanalındayım.")

@bot.command(name="odadan_ayril")
async def odadan_ayril(ctx):
    voice_client = ctx.voice_client
    if voice_client is None or not voice_client.is_connected():
        await ctx.send("Bot herhangi bir ses kanalında değil.")
        return
    
    await voice_client.disconnect()
    await ctx.send("Ses kanalından ayrıldım.")










with open('token.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
