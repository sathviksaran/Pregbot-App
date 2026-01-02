🤰 PregBot – AI Pregnancy Assistant


PregBot is an AI-powered pregnancy assistant that helps expecting mothers with health guidance, daily routines, reminders, multilingual chat, and voice support — available on web and Android.



🌐 Live Demo


🔗 Website

https://pregbot-app.onrender.com


📱 Android App (APK)

Download the latest APK from GitHub Releases:

👉 https://github.com/sathviksaran/pregbot/releases/latest



✨ Features




🤖 AI-powered pregnancy chatbot




🌍 Multilingual support (English, Telugu, Hindi, Tamil, Kannada)




🎤 Voice input (Speech Recognition)




🔊 Voice output (Text-to-Speech)




🩺 Health profile & personalized responses




⏰ Daily routine & reminder emails




📱 Android app (WebView-based APK)




☁️ Cloud-hosted & scalable





🛠️ Tech Stack


Backend




Python (Flask)




SQLAlchemy




MySQL (Railway)




Hugging Face (ML inference)




Brevo (Email service)




Frontend




HTML, CSS, JavaScript




Web Speech API




Browser-based Text-to-Speech




Hosting




Render (Web App)




Hugging Face Spaces (ML model)




Railway (Database)





🚀 Getting Started (Local Setup)


1️⃣ Clone the repository



git clone https://github.com/<your-username>/pregbot.git
cd pregbot




2️⃣ Create virtual environment



python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows




3️⃣ Install dependencies



pip install -r requirements.txt




4️⃣ Set environment variables


Create a .env file:



SECRET_KEY=your_secret_key
DATABASE_URL=mysql+pymysql://user:password@host/db
BREVO_API_KEY=your_brevo_api_key
HF_API_URL=your_huggingface_endpoint
HF_AUTH_TOKEN=your_hf_token_if_private




5️⃣ Run the app



python app.py



Open:



http://127.0.0.1:5000




📱 Android App


The Android app is built using Website 2 APK Builder Pro, wrapping the live web application into a mobile-friendly experience.




No separate backend required




Same API & features as web




Supports voice & multilingual features




APK files are available in the Releases section.



🔐 Security Notes




Secrets are stored using environment variables




API keys are never hardcoded




Internal cron endpoints are protected via secret headers





⚠️ Known Limitations




Firefox does not support Speech Recognition API




Voice output availability depends on browser TTS engines




Free-tier hosting limits apply (Render, HF, Railway)





🗺️ Roadmap




✅ Initial release




🔜 WhatsApp reminders




🔜 Push notifications




🔜 User-specific ML personalization




🔜 Play Store deployment





🤝 Contributing


Contributions are welcome!




Fork the repo




Create a feature branch




Commit changes




Open a Pull Request





📄 License


This project is licensed under the MIT License.



🙌 Author


Sathvik Saran Atchukolu

📧 Email: atchukolus@gmail.com

🌐 GitHub: https://github.com/<your-username>



⭐ Support


If you find this project helpful, please ⭐ star the repository — it really helps!
