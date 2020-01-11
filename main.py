from flask import Flask, request, jsonify
import requests
import re
from pprint import pprint

# GLOBALS
RECIPE_ASK_PATTERN = re.compile(r"([Ww]hat's|[Gg]imme|[Gg]ive me|[Cc]huck me|[Cc]huck us) ((a )?recipe|(some )?food)( cuz)? ?(?P<args>.*)")
RECIPE_CHOICE_PATTERN = re.compile(r"^(?P<choice>[0-9]+)$")
STORAGE_LINK = 'https://store.ncss.cloud/'
INGREDIENTS_API = 'https://store.ncss.cloud/syd-2-foodLists'
app = Flask(__name__)

# APIs
# https://spoonacular.com/food-api/docs
# http://store.ncss.cloud/docs/
# Andrey's testing room: https://chat.ncss.cloud/syd-2-andrey
# Final Product Room: https://chat.ncss.cloud/syd-2-alfred


# Storage Functions
def store_item(key, item):
  room = STORAGE_LINK + str(key)
  resp = requests.post(room, json=item)
  

def get_item(key):
  room = STORAGE_LINK + str(key)
  resp = requests.get(room).json()
  return resp

def add_to_list(key, item):
  room = STORAGE_LINK + str(key)
  data = get_item(key)
  data.append(item)
  store_item(key, data)

def add_to_dict(key, dic_key, dic_value):
  room = STORAGE_LINK + str(key)
  data = get_item(key)
  data[dic_key] = dic_value
  store_item(key, data)




def get_ingredients():
  ingredients = {}
  all_food = requests.get(INGREDIENTS_API).json()
  for section in all_food:
    for food_item in all_food[section]:
      ingredients[food_item] = all_food[section][food_item]
  return ingredients




@app.route('/get_recipe_choice', methods=['POST'])
def get_recipe_choice():
  resp = request.get_json()

  message = resp['text']
  author = resp['author']
  room = resp['room']

  if 'agent' in resp:
    html_break = ' '
  else:
    html_break = '<br>'

  choice = resp['params']['choice']
  recipe_id = get_item(f"syd-2/searched-recipes/{author}/choices")[choice]
  store_item(f"syd-2/searched-recipes/{author}", recipe_id)

  return jsonify({
    'author': 'Alfred',
    'room': room,
    'text': f"Item {choice} selected"
  })




'''
Here I will try make a good regex string

What's a dish I can make(?P<args>)\?
'''




@app.route('/get_recipe', methods=['POST'])
def get_recipe():
  resp = request.get_json()

  message = resp['text']
  print(resp['params'])

  if 'agent' in resp:
    html_break = ' '
  else:
    html_break = '<br>'

  args = resp['params']['string']

  # BELOW IS THE TEST CODE FOR INGREDIENTS
  ingredients = get_ingredients()

  if ingredients == {}:
    return jsonify({
      'author': 'Alfred',
      'room': resp['room'],
      'text': "You don't have any ingredients, silly."
    })

  query = ""
  for ingredient_name in ingredients:
    curr_query = ingredient_name
    quantity = ingredients[ingredient_name]['quantity']
    #below if the ingredients come as quantity only
    #quantity = ingredients[ingredient_name]
    if quantity > 1:
      curr_query += "&number=" + str(quantity)
    curr_query += ',+'
    query += curr_query

  query = query.strip(',+')

  _params = {
    'ingredients': query, 
    'apiKey':'72aef675c4284f2ca32357d241c42284', 
    'number':100
  }

  recipes = requests.get("https://api.spoonacular.com/recipes/findByIngredients", params=_params).json()

  user_recipes = {}
  text = f"Please pick an option by entering a number:{html_break}"

  # invalid_recipes contains the recipes with 2 or more missing ingredients
  invalid_recipes = []

  for i in range(len(recipes)):
    recipe_name = recipes[i]['title']
    recipe_id = recipes[i]['id']
    
    missing_ingredient_count = recipes[i]['missedIngredientCount']
    print(missing_ingredient_count)

    if missing_ingredient_count == 0:
      user_recipes[i+1] = recipe_id
      text += f'{i+1}: {recipe_name}{html_break}'
      print("work0")
    elif missing_ingredient_count <= 5:
      missing_ingredient = recipes[i]['missedIngredients'][0]['name']
      user_recipes[i+1] = recipe_id
      text += f'{i+1}: {recipe_name}, missing {missing_ingredient}{html_break}'
      print("work1")
    else:
      invalid_recipes.append(recipes[i])

  store_item(f"syd-2/searched-recipes/{resp['author']}/choices", user_recipes)
  text = text.strip(f'{html_break}')

  print(text)

  return jsonify({
    'author': 'Alfred',
    'room': resp['room'],
    'text': text
  })




app.run(host='0.0.0.0', port=8080, debug=True)
