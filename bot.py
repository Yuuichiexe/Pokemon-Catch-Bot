import os
import requests
from pymongo import MongoClient
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Connect to MongoDB
client = MongoClient('mongodb+srv://sonu55:sonu55@cluster0.vqztrvk.mongodb.net/?retryWrites=true&w=majority')
db = client['waifu_bot']
collection = db['waifus']

# Create a Pyrogram client
api_id = 10536941
api_hash = 'c78f516b3edf45f38277755da7f52128'
bot_token = '5842642941:AAHkXH9rD11b7qWingnz8tlC-DerRPDxSZI'
app = Client("waifu_bot", api_id, api_hash, bot_token=bot_token)


# Admin panel
admin_panel = {
    "add_anime": False,
    "add_waifu": False,
    "current_anime": None
}

# Handler function for /addanime command
@app.on_message(filters.command("addanime"))
def add_anime(client, message):
    user_id = message.from_user.id
    if user_id == 2033411815:
        admin_panel["add_anime"] = True
        message.reply_text("Enter the name of the anime you want to add:")


# Handler function for /addwaifu command
@app.on_message(filters.command("addwaifu"))
def add_waifu(client, message):
    user_id = message.from_user.id
    if user_id == 2033411815:
        admin_panel["add_waifu"] = True
        message.reply_text("Enter the name of the waifu you want to add:")


# Handler function for group messages
@app.on_message(filters.group)
def group_message(client, message):
    # Handle group messages here
    pass


# Handler function for private messages
@app.on_message(filters.private)
def private_message(client, message):
    user_id = message.from_user.id
    user_input = message.text.lower()

    # Admin panel
    if user_id == 2033411815:
        if user_input == "/admin":
            show_admin_panel(message)
        elif admin_panel["add_anime"]:
            add_new_anime(message)
        elif admin_panel["add_waifu"]:
            add_new_waifu(message)


# Show admin panel options
def show_admin_panel(message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Add Anime", callback_data="add_anime")],
            [InlineKeyboardButton("Add Waifu", callback_data="add_waifu")]
        ]
    )
    message.reply_text("Admin Panel:", reply_markup=keyboard)


# Add new anime
def add_new_anime(message):
    anime_name = message.text
    collection.insert_one({"name": anime_name})
    admin_panel["add_anime"] = False
    admin_panel["current_anime"] = anime_name
    message.reply_text(f"Anime '{anime_name}' added successfully. Now add waifus to this anime.")


# Add new waifu
def add_new_waifu(message):
    waifu_name = message.text
    waifu_photos = message.photo

    if waifu_photos:
        # Download waifu photos
        file_id = waifu_photos[-1].file_id
        file_path = app.download_media(file_id, file_name=f"waifu_{waifu_name}")

        # Save waifu to the database
        anime_name = admin_panel["current_anime"]
        collection.update_one({"name": anime_name}, {"$push": {"waifus": {"name": waifu_name, "photo_path": file_path}}})

        # Remove downloaded file
        os.remove(file_path)

        message.reply_text(f"Waifu '{waifu_name}' added successfully to anime '{anime_name}'.")
    else:
        message.reply_text("Please provide at least one photo of the waifu.")


# Start the bot
app.run()
