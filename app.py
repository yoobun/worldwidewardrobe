from flask import Flask
from flask import render_template
from flask import Response, request, jsonify

import requests
import time
import bs4 as bs
from selenium import webdriver
app = Flask(__name__)

#chatgpt
import os
import openai

#images
import json
from base64 import b64decode
from pathlib import Path

import key
openai.api_key = key.SECRET_KEY

style_data = {
    "likes": "",
    "styles": "",
    "brands": "",
    "suggestions": [],
    "recommendations": [
        {
            "brand": "",
            "imgs": []
        },
        {
            "brand": "",
            "imgs": []
        },
        {
            "brand": "",
            "imgs": []
        },
        {
            "brand": "",
            "imgs": []
        },
        {
            "brand": "",
            "imgs": []
        },
    ]
}

#set likes
@app.route('/user-likes', methods=['GET', 'POST'])
def submit_user_likes():
    global style_data

    data = request.get_json()
    
    style_data["likes"] = data["likes"]

    return jsonify(style_data)

#set styles
@app.route('/user-styles', methods=['GET', 'POST'])
def submit_user_styles():
    global style_data
    
    data = request.get_json()
    
    style_data["styles"] = data["styles"]

    print(style_data['styles'])

    return jsonify(style_data)

#style_suggestions
@app.route('/style_suggestions', methods=['GET', 'POST'])
def get_suggestions():
    global style_data

    likes = style_data["likes"]
    styles = style_data["styles"]

    print(style_data['likes'] + " " + style_data["styles"])

    style_sug = get_suggestions_for_expansion(likes, styles)
    style_data["suggestions"] = style_sug

    json_string = json.dumps(style_data, indent=2)
    print(json_string)

    return jsonify(style_data)

def parse_response_from_gpt(gpt_response):
    output = gpt_response.splitlines()

    new_responses = []
    for i, response in enumerate(output):
        response = response.strip()
        if response != "":
            new_responses.append(response)
    print(new_responses)
    return new_responses

def get_suggestions_for_expansion(likes, styles):
    gpt_prompt = "I like to wear "+likes+" and "+styles+" styles. Give me 5 style suggestions like this in short paragraph format: 1. [suggestions] 2. [suggestion] 3. [suggestion]"
    print(gpt_prompt)

    response = openai.ChatCompletion.create (
        model="gpt-4-1106-preview",
        messages = [
            {'role': 'system', 
             'content': 'You are my stylist'},
            {'role': 'user', 
             'content': gpt_prompt}
        ],
        temperature=1,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    output = response['choices'][0]['message']['content']
    print(output)

    #parsing
    suggestion_output = []
    try:
        suggestion_output = parse_response_from_gpt(output)
        #output = suggestion_output[1:]

    except:
        print("ERROR: unable to parse from gpt")
        print(response)
    return suggestion_output

#set user brands
@app.route('/submit_brands', methods=["GET", "POST"])
def submit_brands():
   data = request.get_json()
   
   style_data["brands"] = data["brands"]
   
   return jsonify(style_data)

#gets brand suggestions
@app.route('/brand_suggestions', methods=['GET', 'POST'])
def get_brands_list():
    global style_data

    brands = style_data["brands"]
    styles = style_data["styles"]

    brands_list = get_brands_expansion(brands, styles)

    for i in range(5):
        style_data["recommendations"][i]["brand"] = brands_list[i]

    brand_name = parse_brand_for_imgs(brands_list)
    brand_imgs = get_brand_images(brand_name)

    for i in range(5):
        style_data["recommendations"][i]["imgs"] = brand_imgs[i]

    json_string = json.dumps(style_data, indent=2)

    print(json_string)

    return jsonify(style_data)

def get_brands_expansion(brands, styles):
    gpt_prompt = "Give me 5 lesser known "+styles+" brands similar to "+brands+". Give me 5 suggestions like this: 1. [brand name]:[brand description], 2. [brand name]:[brand description], 3. [brand name]:[brand description]."
    print(gpt_prompt)

    response = openai.ChatCompletion.create (
        model="gpt-4-1106-preview",
        messages = [
            {'role': 'system', 
             'content': 'You are my stylist'},
            {'role': 'user', 
             'content': gpt_prompt}
        ],
        temperature=1,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    output = response['choices'][0]['message']['content']

    #parsing
    suggestion_output = []
    try:
        suggestion_output = parse_response_from_gpt(output)
    except:
        print("ERROR: unable to parse brands from gpt")
        print(response)

    return suggestion_output

def parse_brand_for_imgs(brands_output):
    new_brands = []
    if len(new_brands) <= 5:
        for brand in brands_output:
            brand_name = brand.split(":")[0]
            stripped = brand_name[3:]
            new_brands.append(stripped)
    print(new_brands)
    return new_brands

def get_brand_images(brands_output):
    queries = []
    url = "https://www.pinterest.co.uk/search/pins/?rs=typo_auto_original&q="
    for brand in brands_output:
        brand = brand.replace(" ", "%20").lower() + "%20clothing&auto_correction_disabled=true"
        query = url + brand
        print(query)
        queries.append(query)

    driver = webdriver.Chrome()
    
    imgs_brands = []
    for query in queries:
        driver.get(query)
        time.sleep(5)
        src = driver.page_source
        finder = bs.BeautifulSoup(src, features="html.parser")
        img = finder.find_all('img')

        imgs = []
        for link in img:
            src_attr = link.get('src')
            imgs.append(src_attr)
        only = imgs[:5]
        imgs_brands.append(only)
    
    print(imgs_brands)
    return imgs_brands

@app.route("/explore_brands", methods=['GET', 'POST'])
def explore_brands():
    return jsonify(style_data)    

@app.route("/build-my-style", methods=['GET', 'POST'])
def build_my_style():
    return jsonify(style_data)

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/likes")
def likes():
    return render_template('style_builder.html', data=style_data)

@app.route("/styles")
def styles():
    return render_template('style_builder2.html', data=style_data)

@app.route("/suggestions")
def suggestions():
    return render_template('style_suggestions.html', data=style_data)

@app.route("/brand_styles") 
def brand_styles():
    return render_template('brand_styles.html', data=style_data)

@app.route("/brands")
def brands():
    return render_template("brands.html", data=style_data)

@app.route("/recommendations")
def recommendations():
    return render_template('recommended_brands.html', data=style_data)

if __name__ == '__main__':
    app.run(debug = True, port = 8000)    
    #app.run(debug = True)
