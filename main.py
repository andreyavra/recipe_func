from flask import Flask, request, jsonify
import requests
import re

# GLOBALS
RECIPE_ASK_PATTERN = re.compile(r"([Ww]hat's|[Gg]imme|[Gg]ive me|[Cc]huck me|[Cc]huck us) ((a )?recipe|(some )?food)( cuz)? ?(?P<args>.*)")
RECIPE_CHOICE_PATTERN = re.compile(r"^(?P<choice>[0-9]+)$")
STORAGE_LINK = 'https://store.ncss.cloud/'
app = Flask(__name__)

# APIs
# https://spoonacular.com/food-api/docs
# http://store.ncss.cloud/docs/
# Andrey's testing room: https://chat.ncss.cloud/syd-2-andrey
# Final Product Room: https://chat.ncss.cloud/syd-2-alfred


# Storage Functions
def store_item(key, item):
  room = STORAGE_LINK + str(key)
  print(item)
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








@app.route('/get_recipe_choice', methods=['POST'])
def get_recipe_choice():
  args = request.get_json()

  message = args['text']
  author = args['author']
  room = args['room']

  m = RECIPE_CHOICE_PATTERN.match(message)
  if m is None:
    text = "That isn't a valid response. Please try again. Select an option from 1 to 20"
    return jsonify({
      'author': 'Chef Bot',
      'room': args['room'],
      'text': text
    })
  else:
    choice = m.group('choice')
    recipe_id = get_item(f"syd-2/searched-recipes/{args['author']}/choices")[choice]
    print("4work")
    store_item(f"syd-2/searched-recipes/{args['author']}", recipe_id)

    return jsonify({
      'author': 'Chef Bot',
      'room': args['room'],
      'text': f"Item {choice} selected"
    })









@app.route('/get_recipe', methods=['POST'])
def get_recipe():
  resp = request.get_json()

  message = resp['text']


  m = RECIPE_ASK_PATTERN.match(message)
  if m is None:
    print("INCORRECT AI YA")

  else:
    args = m.group('args')

    # BELOW IS THE TEST CODE FOR INGREDIENTS
    ingredients = {
      'cheese':{'quantity':2, 'expiration': '04042019'},
      'chicken':{'quantity':1, 'expiration': '05052020'}
    }

    query = ""
    for ingredient_name in ingredients:
      curr_query = ingredient_name
      quantity = ingredients[ingredient_name]['quantity']
      if quantity > 1:
        curr_query += "&number=" + str(quantity)
      curr_query += ',+'
      query += curr_query

    query = query.strip(',+')

    print(query)

    _params = {
      'ingredients': query, 
      'apiKey':'72aef675c4284f2ca32357d241c42284', 
      'number':20
    }

    recipes = requests.get("https://api.spoonacular.com/recipes/findByIngredients", params=_params).json()
      
    user_recipes = {}
    text = "Please pick an option by entering a number:<br>"

    for i in range(len(recipes)):
      title = recipes[i]['title']
      recipe_id = recipes[i]['id']
      user_recipes[i+1] = recipe_id

      text += f'{i+1}: {title}<br>'

    store_item(f"syd-2/searched-recipes/{resp['author']}/choices", user_recipes)
    text = text.strip('<br>')

    return jsonify({
      'author': 'Chef Bot',
      'room': resp['room'],
      'text': text
    })




app.run(host='0.0.0.0', port=8080, debug=True)
