import os
import subprocess
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from gtts import gTTS

client = genai.Client(api_key="AQ.Ab8RN6IqaNoAhTylGhgIPgvzHxrdr_TK-DoIqQh_95rDha79mQ")

def translate_audio_with_gemini(audio_file_path):
    audio_file = client.files.upload(file=audio_file_path)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            audio_file,
            "សូមស្ដាប់សំឡេងក្នុងឯកសារនេះ បកប្រែអត្ថន័យទាំងស្រុងមកជាភាសាខ្មែរធម្មជាតិ សម្រាប់យកទៅអានចេញសំឡេងបន្ត។ សូមផ្ដល់តែអត្ថបទបកប្រែជាភាសាខ្មែរសុទ្ធសាធបានហើយ。"
        ]
    )
    return response.text

def process_video_dubbing(input_video_path, output_video_path):
    extracted_audio = "temp_audio.mp3"
    khmer_audio = "khmer_voice.mp3"

    try:
        extract_cmd = ['ffmpeg', '-y', '-i', input_video_path, '-q:a', '0', '-map', 'a', extracted_audio]
        subprocess.run(extract_cmd, check=True)

        khmer_text = translate_audio_with_gemini(extracted_audio)

        tts = gTTS(text=khmer_text, lang='km', slow=False)
        tts.save(khmer_audio)

        merge_cmd = [
            'ffmpeg', '-y', '-i', input_video_path, '-i', khmer_audio,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            output_video_path
        ]
        subprocess.run(merge_cmd, check=True)
    finally:
        for f in [extracted_audio, khmer_audio]:
            if os.path.exists(f):
                os.remove(f)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_file = update.message.video or update.message.document
    if not user_file:
        await update.message.reply_text("សូមផ្ញើមកជាទម្រង់ ឯកសារវីដេអូ (Video) ប៉ុណ្ណោះ!")
        return

    status_msg = await update.message.reply_text("⏳ កំពុងប្រើប្រាស់ Gemini AI ដើម្បីបកប្រែសំឡេង និងដូរជាភាសាខ្មែរ... សូមរង់ចាំបន្តិច។")

    file = await context.bot.get_file(user_file.file_id)
    input_path = "input_video.mp4"
    output_path = "output_khmer_video.mp4"
    await file.download_to_drive(input_path)

    try:
        process_video_dubbing(input_path, output_path)
        await update.message.reply_video(
            video=open(output_path, 'rb'),
            caption="✅ វីដេអូរបស់អ្នកត្រូវបានប្ដូរសំឡេងមកជាភាសាខ្មែរជោគជ័យ!"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ មានបញ្ហាក្នុងការដំណើរការ៖ {str(e)}")
    finally:
        for p in [input_path, output_path]:
            if os.path.exists(p):
                os.remove(p)
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=status_msg.message_id)

app = ApplicationBuilder().token("8846112799:AAHXZF3auIn47a9MsK0kLmAzY6BkOrEJYvQ").build()
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

print("🤖 Bot កំពុងដំណើរការ...")
app.run_polling()
