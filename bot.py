import os
import random
import requests
from pymongo import MongoClient
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Connect to MongoDB
client = MongoClient('mongodb+srv://sonu55:sonu55@cluster0.vqztrvk.mongodb.net/?retryWrites=true&w=majority')
db = client['pokemon_bot']
collection = db['pokedex']
anime_collection = db['anime']

# Database of available Pokémon
pokemon_database = [
    {"name": "Bulbasaur", "catch_rate": 45},
    {"name": "Ivysaur", "catch_rate": 45},
    {"name": "Venusaur", "catch_rate": 45},
]

# Global variables to track the group message count and the currently announced Pokémon
message_count = 0
announced_pokemon = None

# Create a Pyrogram client
api_id = 10536941
api_hash = 'c78f516b3edf45f38277755da7f52128'
bot_token = '5842642941:AAHkXH9rD11b7qWingnz8tlC-DerRPDxSZI'
app = Client("pokemon_bot", api_id, api_hash, bot_token=bot_token)


# Global variables to track the announced Pokémon and caught Pokémon
announced_pokemon = None
caught_pokemon = {}

# Admin panel
admin_panel = {
    "add_anime": False,
    "add_waifu": False,
    "current_anime": None
}

# Handler function for /catch command
@app.on_message(filters.command("catch"))
def catch_pokemon(client, message):
    global announced_pokemon  # Declare announced_pokemon as a global variable
    user_id = message.from_user.id
    user_input = message.text
    pokemon_name = user_input.split("/catch ", 1)[-1].lower()

    # Check if a Pokémon is currently announced
    if announced_pokemon is None:
        client.send_message(chat_id=message.chat.id, text="No Pokémon is currently announced.", reply_to_message_id=message.message_id)
        return

    # Check if the caught Pokémon matches the announced Pokémon
    if pokemon_name.lower() == announced_pokemon["name"].lower():

        # Check if the Pokémon has already been caught
        if announced_pokemon["name"] in caught_pokemon:
            client.send_message(chat_id=message.chat.id, text="{} has already been caught.".format(announced_pokemon["name"], reply_to_message_id=message.message_id))
            return

        catch_probability = random.random()

        if catch_probability <= announced_pokemon["catch_rate"]:
            client.send_message(chat_id=message.chat.id, text="Congratulations [{}](tg://user?id={})! You caught {}!".format(message.from_user.first_name, message.from_user.id, announced_pokemon["name"], parse_mode="Markdown", reply_to_message_id=message.message_id))
            add_to_pokedex(user_id, announced_pokemon["name"])

            # Add the caught Pokémon and the user who caught it to the dictionary
            caught_pokemon[announced_pokemon["name"]] = user_id

            # Set announced_pokemon to None to allow the announcement of a new Pokémon
            announced_pokemon = None
        else:
            client.send_message(chat_id=message.chat.id, text="Oh no! {} escaped!".format(announced_pokemon["name"], reply_to_message_id=message.message_id))
    else:
        client.send_message(chat_id=message.chat.id, text="The announced Pokémon is not {}.".format(pokemon_name), reply_to_message_id=message.message_id)


# Handler function for group messages
@app.on_message(filters.group)
def group_message(client, message):
    global message_count, announced_pokemon

    message_count += 1

    if message_count % 2 == 0:
        announced_pokemon = random.choice(pokemon_database)
        pokemon_data = pokemon(announced_pokemon["name"].lower())
        pokemon_image_url = pokemon_data.sprites.front_default

        # Download the Pokémon image
        image_response = requests.get(pokemon_image_url)
        image_file_name = f"{announced_pokemon['name']}.png"
        with open(image_file_name, 'wb') as image_file:
            image_file.write(image_response.content)

        # Send the Pokémon image and announcement message
        client.send_photo(message.chat.id, photo=image_file_name, caption="A wild {} appeared! Type '/catch {}' to catch it.".format(announced_pokemon["name"], announced_pokemon["name"]))

        # Remove the downloaded image file
        image_file.close()
        os.remove(image_file_name)


# Handler function for private messages
@app.on_message(filters.private)
def private_message(client, message):
    user_id = message.from_user.id
    user_input = message.text.lower()

    # Admin panel
    if user_id == YOUR_ADMIN_USER_ID:
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
    anime_collection.insert_one({"name": anime_name})
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
        anime_collection.update_one({"name": anime_name}, {"$push": {"waifus": {"name": waifu_name, "photo_path": file_path}}})

        # Remove downloaded file
        os.remove(file_path)

        message.reply_text(f"Waifu '{waifu_name}' added successfully to anime '{anime_name}'.")
    else:
        message.reply_text("Please provide at least one photo of the waifu.")


# Function to add a caught Pokémon to the user's Pokedex
def add_to_pokedex(user_id, pokemon_name):
    pokedex_data = collection.find_one({"user_id": user_id})
    if pokedex_data:
        pokedex = pokedex_data['pokedex']
        if pokemon_name not in pokedex:
            pokedex.append(pokemon_name)
        collection.update_one({"user_id": user_id}, {"$set": {"pokedex": pokedex}})
    else:
        collection.insert_one({"user_id": user_id, "pokedex": [pokemon_name]})


# Start the bot
app.run()
    
