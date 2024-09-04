#pip install openai

import openai
import time
import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import requests
import json
import re


os.getenv("OPENAI_API_KEY")
api_key = os.getenv("ELEVENLABS_API_KEY")

# Initialize the client
client = openai.OpenAI()

from openai import OpenAI
client = OpenAI()

'''Initialising relevant variables'''

topic = str(input("Enter the name of the topic "))
num_facts = str(input("Enter the number of facts "))

content = "This is the topic"+ topic + "Your job is to generate" + num_facts +  "unknown/less known/mysterious facts about the topic. Please only give facts as a numbered list like 1. Fact 1 2. Fact 2 3. Fact 3 and so on"


'''1. Generating facts using OpenAI'''

def generate_facts(content, num_facts):

    completion = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {"role": "system", "content": "You are a universe facts generator"},
        {"role": "user", "content": content}
      ]
    )
    response = completion.choices[0].message.content
    return response
    

#Calling generate_facts function to get generated facts
generated_facts = generate_facts(content, num_facts)
print("The generated facts are ", generated_facts)

# Split the string based on the pattern of "number + dot + space"
facts_array = re.split(r'\d+\.\s+', generated_facts)

# Remove any empty strings that may result from splitting
facts_array = [fact.strip() for fact in facts_array if fact.strip()]

# Print the result
print("The facts array is", facts_array)






'''2. Converting text to voice using Elevenlabs'''

#Defining submit text function
def submit_text(fact):
    url = "https://api.elevenlabs.io/v1/text-to-speech/pMsXgVXv3BLzUgSXRplE"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": fact,
        "voice_settings": {
            "stability": 0.1,
            "similarity_boost": 0
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print("Success:", response.content)
    else:
        print(f"Error {response.status_code}: {response.content}")


#Hitting Get Generated Items to get the history_id
#Defining get history item id function
def get_history_item_id():
    client = ElevenLabs(
    api_key=api_key,
)
    resp = client.history.get_all(
        page_size=1,
        voice_id="pMsXgVXv3BLzUgSXRplE",

    )

    history_item_id = resp.history[0].history_item_id
    return history_item_id

def create_audiofile(count, history_item_id):
    client = ElevenLabs(
    api_key=api_key,
)
    # Getting the audio generator
    audio_generator = client.history.get_audio(
        history_item_id=str(history_item_id),
    )
    filename = str(count)+".mp3"
    # Saving the audio data to a file
    with open(filename, "wb") as audio_file:
        for chunk in audio_generator:
            audio_file.write(chunk)

    print(filename+ "saved successfully")



print("The length of facts array is ", len(facts_array))

count = 0

for fact in facts_array:
    print("This is the fact", fact)
    submit_text(str(fact))
    print("text submitted for voice conversion")
    history_id= get_history_item_id()
    print("The history id is ", history_id)
    create_audiofile(count, history_id)
    count = count+1

    
    
#To do file structure where the audios are saved
#Get the length of audio file
#Split video according to length of audio files and save in a different folder
#Run loop to compile the final videos
# Add background music

