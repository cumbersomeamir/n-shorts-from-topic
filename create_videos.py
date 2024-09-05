#pip install openai elevenlabs pydub moviepy

import openai
import time
import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import requests
import json
import re
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import random


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

# Initialize an array to store the durations
durations = []

def create_audiofile(count, history_item_id):
    output_folder = "trimmed_audio"
    client = ElevenLabs(
        api_key=api_key,
    )
    
    # Getting the audio generator
    audio_generator = client.history.get_audio(
        history_item_id=str(history_item_id),
    )
    
    # Generate a unique ID for the filename
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.mp3"
    
    # Full path to save the file in the trimmed_audio folder
    file_path = os.path.join(output_folder, filename)
    
    # Saving the audio data to a file
    with open(file_path, "wb") as audio_file:
        for chunk in audio_generator:
            audio_file.write(chunk)

    # Load the saved audio file to get its duration
    audio = AudioSegment.from_file(file_path)
    duration = len(audio) / 1000  # Duration in seconds
    durations.append(duration)  # Append duration to the list

    print(f"{file_path} saved successfully, duration: {duration} seconds")
    

# At the end of your process, you'll have the `durations` array with all the lengths



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
print("All the durations are ", durations)
print("Type of durations is ", type(durations))
#Split video according to length of audio files and save in a different folder
def trim_and_save_clips(input_video, durations, output_folder):
    # Load the video file
    video = VideoFileClip(input_video)

    # Create a list to store the trimmed clips
    trimmed_clips = []

    # Starting point of the trim
    start_time = 0

    # Check if output folder exists, if not create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over the durations array and create trimmed clips
    for duration in durations:
        end_time = start_time + duration
        # Extract the clip from start_time to end_time
        trimmed_clip = video.subclip(start_time, end_time)
        trimmed_clips.append(trimmed_clip)
        # Update start_time for the next trim
        start_time = end_time

    # Save the trimmed clips as new video files with unique IDs
    for clip in trimmed_clips:
        unique_id = str(uuid.uuid4())  # Generate a unique ID
        output_filename = os.path.join(output_folder, f"trimmed_clip_{unique_id}.mp4")
        clip.write_videofile(output_filename, codec="libx264")

    # Close the video and clips to free up resources
    video.close()
    for clip in trimmed_clips:
        clip.close()

# Example usage:
input_video = "youtube_video.mp4"
output_folder = "trimmed_clips"

trim_and_save_clips(input_video, durations, output_folder)

#Run loop to compile the final videos


def combine_video_audio(trimmed_clips_dir, trimmed_audio_dir, combined_media_dir):
    # Helper function to filter out non-media files
    def is_media_file(filename):
        return filename.lower().endswith(('.mp4', '.mp3'))  # Modify this if you have other formats
    
    # Get the list of video and audio files, filtering out non-media files
    video_files = sorted([f for f in os.listdir(trimmed_clips_dir) if is_media_file(f)])
    audio_files = sorted([f for f in os.listdir(trimmed_audio_dir) if is_media_file(f)])
    
    # Ensure both directories have the same number of files
    if len(video_files) != len(audio_files):
        raise ValueError("The number of video files and audio files do not match.")
    
    # Loop through the files and combine them
    for video_file, audio_file in zip(video_files, audio_files):
        # Construct full file paths
        video_path = os.path.join(trimmed_clips_dir, video_file)
        audio_path = os.path.join(trimmed_audio_dir, audio_file)
        
        # Load video and audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        # Combine video and audio
        final_clip = video_clip.set_audio(audio_clip)
        
        # Save the final output
        output_path = os.path.join(combined_media_dir, video_file)
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # Close clips to free up resources
        video_clip.close()
        audio_clip.close()

# Example usage
combine_video_audio("trimmed_clips", "trimmed_audio", "combined_media")
# Create folder with different background music



def add_background_music_to_videos(combined_media_dir, background_music_file, final_media_dir):
    # Ensure the output directory exists
    if not os.path.exists(final_media_dir):
        os.makedirs(final_media_dir)

    # Load the background music
    background_music = AudioFileClip(background_music_file)
    
    # Get the duration of the background music
    music_duration = background_music.duration

    # Process each video in the combined_media directory
    for video_file in os.listdir(combined_media_dir):
        if video_file.endswith('.mp4'):
            video_path = os.path.join(combined_media_dir, video_file)
            
            # Load the video
            video = VideoFileClip(video_path)
            
            # Get the duration of the video
            video_duration = video.duration
            
            # Calculate the latest possible start time for the background music
            latest_start = max(0, music_duration - video_duration - 60)
            
            # Choose a random start time for the background music
            music_start_time = random.uniform(0, latest_start)
            
            # Extract the portion of background music we need
            music_clip = background_music.subclip(music_start_time, music_start_time + video_duration)
            
            # Adjust the volume of the background music (e.g., to 20% of its original volume)
            music_clip = music_clip.volumex(0.2)
            
            # Combine the original audio and the background music
            final_audio = CompositeAudioClip([video.audio, music_clip])
            
            # Set the final audio to the video
            final_video = video.set_audio(final_audio)
            
            # Generate the output file path
            output_path = os.path.join(final_media_dir, f"final_{video_file}")
            
            # Write the final video file
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            # Close the clips to free up resources
            video.close()
            final_video.close()

    # Close the background music clip
    background_music.close()

# Example usage
add_background_music_to_videos("combined_media", "background_music.mp3", "final_media")


#Add support for captions

