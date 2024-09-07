from openai import OpenAI
import os
import cProfile

client = OpenAI()

audio_file= open("data/1 minute sugar recording.mp3", "rb")
def transcribe_audio(audio_file):
    transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file
    )
    return transcript

#cProfile.run('transcribe_audio(audio_file)', sort='cumtime')

transcript = transcribe_audio(audio_file)
print(transcript.text)

def summarize_text(text, model):
    completion = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You should summarize the following text:"},
        {"role": "user", "content": text}
    ]
    )
    return completion.choices[0].message

cProfile.run('summarize_text(transcript.text, "gpt-4o")', sort='cumtime')
cProfile.run('summarize_text(transcript.text, "gpt-4o-mini")', sort='cumtime')

summarized_text_gpt_4o = summarize_text(transcript.text, "gpt-4o")
summarized_text_gpt_4o_mini = summarize_text(transcript.text, "gpt-4o-mini")