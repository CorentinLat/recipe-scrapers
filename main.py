import json
import re
import requests
import sys
import urllib.parse
import uuid

# import subprocess

from urllib.request import urlopen
from recipe_scrapers import scrape_html

MEALIE_API_URL = "http://localhost:9925/api"
MEALIE_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb25nX3Rva2VuIjp0cnVlLCJpZCI6ImI2MTZkOWNkLWI3ZTAtNGI4Ny1hMjc2LWNhOTgwMzcwNjYzMiIsIm5hbWUiOiJJbXBvcnRYUHl0aG9uIiwiaW50ZWdyYXRpb25faWQiOiJnZW5lcmljIiwiZXhwIjoxODk3MTYzMjAwfQ.cJ1vd6KUTcPXJrcIe0Hq7DpXHGNn0mm4zS45O9b1JME"


def get_paginated_resources_from_mealie_api(get_url):
    resources = []
    page = 1
    has_more = True
    while has_more:
        response = requests.get(get_url + "?" + urllib.parse.urlencode({"page": page}),
                                headers={"Authorization": f"Bearer {MEALIE_API_TOKEN}"})
        response_json = response.json()
        resources.extend(response_json["items"])
        has_more = int(response_json["page"] < response_json["total_pages"])
        page += 1

    return resources


def post_data_to_mealie_api(post_url, data):
    response = requests.post(post_url, json=data, headers={"Authorization": f"Bearer {MEALIE_API_TOKEN}"})
    return response.json()


def patch_data_to_mealie_api(patch_url, data):
    response = requests.patch(patch_url, json=data, headers={"Authorization": f"Bearer {MEALIE_API_TOKEN}"})
    return response.json()


def get_all_mealie_foods():
    return list(map(lambda u: {"id": u["id"], "name": u["name"]},
                    get_paginated_resources_from_mealie_api(MEALIE_API_URL + "/foods")))


def get_all_mealie_units():
    return list(map(lambda u: {"id": u["id"], "name": u["name"]},
                    get_paginated_resources_from_mealie_api(MEALIE_API_URL + "/units")))


def add_resource_to_mealie_api(resource_name, name):
    post_response = post_data_to_mealie_api(MEALIE_API_URL + f"/{resource_name}", {"name": name})

    if "id" in post_response:
        return post_response["id"]

    print(f"Error adding resource {resource_name} with name {name}: {post_response}")
    sys.exit(1)


def get_resource_id_by_name(resource_name, resources, name):
    for resource in resources:
        if resource["name"] == name:
            return resource["id"]

    print(f"Resource {resource_name} with name {name} not found, creating it")
    new_resource_id = add_resource_to_mealie_api(resource_name, name)
    print(f"Resource {resource_name} with name {name} created with id {new_resource_id}")
    resources.append({"id": new_resource_id, "name": name})
    return new_resource_id


foods = get_all_mealie_foods()
units = get_all_mealie_units()

tags = []
url = ""
url_opened = urlopen(url)
html = url_opened.read().decode(url_opened.headers.get_content_charset())

scraper = scrape_html(html, org_url=url)

recipe_json = scraper.to_json()
recipe_json_str = json.dumps(recipe_json, indent=4)
# print(recipe_json_str)

classic_ingredient_regex = r"^(\d+\.?\d*)\s+(\S+)\s+(.+)$"
gout_ingredient_regex = r".+(gout|goût|go\\u00fbt)\s+(.*)$"
ingredients_formatted = []
for ingredient in recipe_json["ingredients"]:
    reference_id = str(uuid.uuid4())

    ingredient = ingredient.replace("¼", "0.25")
    ingredient = ingredient.replace("⅓", "0.33")
    ingredient = ingredient.replace("½", "0.5")
    ingredient = ingredient.replace("⅗", "0.6")
    ingredient = ingredient.replace("⅔", "0.67")
    ingredient = ingredient.replace("¾", "0.75")

    if res := re.match(classic_ingredient_regex, ingredient):
        quantity, unit, food = res.groups()

        unit_id = get_resource_id_by_name("units", units, unit)
        food_id = get_resource_id_by_name("foods", foods, food)

        ingredients_formatted.append({
            "quantity": float(quantity),
            "unit": {"id": unit_id, "name": unit},
            "food": {"id": food_id, "name": food},
            "referenceId": reference_id
        })
    elif res := re.match(gout_ingredient_regex, ingredient):
        _, food = res.groups()

        food_id = get_resource_id_by_name("foods", foods, food)

        ingredients_formatted.append({
            "quantity": 0,
            "food": {"id": food_id, "name": food},
            "referenceId": reference_id
        })
    else:
        print(f"Could not match ingredient: {ingredient}")
        # sys.exit(1)

instructions_formatted = []
advice_regex = r"((?:[A-Z']+\s+)+:)"
for instruction in recipe_json["instructions_list"]:
    text = instruction
    if res := re.search(advice_regex, instruction):
        print(f"Advice found: {res.group(1)}")
        advice = res.group(1)
        text = instruction.replace(advice, "\n\n**" + advice + "**")

    instructions_formatted.append({"text": text, "ingredientReferences": []})

if "boeuf" in recipe_json["title"].lower() or "bœuf" in recipe_json["title"].lower() or "steak" in recipe_json["title"].lower():
    tags.append({"id": "a4e70465-4136-4eea-b2f6-b15173b9f665", "name": "boeuf", "slug": "boeuf"})
if "poulet" in recipe_json["title"].lower():
    tags.append({"id": "7bdb9b6e-d495-45ab-ae25-79709480054b", "name": "poulet", "slug": "poulet"})
if "porc" in recipe_json["title"].lower() or "saucisse" in recipe_json["title"].lower():
    tags.append({"id": "6a484d30-3ee7-460d-989a-6c74841b8b56", "name": "porc", "slug": "porc"})
if "potatoe" in recipe_json["title"].lower() or "frite" in recipe_json["title"].lower():
    tags.append({"id": "d6430d9f-a542-4edc-bb16-e7c1bd94fe5c", "name": "frites", "slug": "frites"})
# if "riz" in recipe_json["title"].lower():
tags.append({"id": "76086a0c-8c8c-4a5d-aec2-ae75502171b0", "name": "riz", "slug": "riz"})
if "risotto" in recipe_json["title"].lower():
    tags.append({"id": "e273ba74-3988-4f62-adc7-21faaf6fe12d", "name": "risotto", "slug": "risotto"})

valid_json = {
    "description": recipe_json["description"],
    "orgURL": recipe_json["canonical_url"],
    "totalTime": f'{recipe_json["total_time"]} minutes',
    "prepTime": f'{recipe_json["prep_time"]} minutes',
    "recipeServings": 2,
    "recipeIngredient": ingredients_formatted,
    "recipeInstructions": instructions_formatted,
    "recipeCategory": [{"id": "98f14e76-273b-437d-a79d-ed796d88b2ca", "name": "HelloFresh", "slug": "hellofresh"}],
    "tags": tags
}

valid_json_str = json.dumps(valid_json, indent=4)
# print(valid_json_str)

# subprocess.run("pbcopy", text=True, input=valid_json_str)

create_response = post_data_to_mealie_api(MEALIE_API_URL + "/recipes", {"name": recipe_json["title"]})
recipe_slug = create_response

patch_data_to_mealie_api(MEALIE_API_URL + f"/recipes/{recipe_slug}", valid_json)
post_data_to_mealie_api(MEALIE_API_URL + f"/recipes/{recipe_slug}/image", {"url": recipe_json["image"]})

print(f"Recipe created with slug {recipe_slug}")
