from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Crop, UserProfile
from datetime import date
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import google.generativeai as genai
import os
from django.core.files.storage import default_storage
from PIL import Image

from .models import Crop, ImageAnalysis  # <- (see next section for model)




def homepage(request):
    return render(request, 'home.html')

def signup_view(request):
    if request.method == 'POST' and request.POST.get('submit') == 'Sign Up':
        email = request.POST.get('email')
        password = request.POST.get('password')
        fullname = request.POST.get('fullname')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered.")
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=fullname
            )
            login(request, user)
            return redirect('dashboard')

    return render(request, 'registration/login.html')

def login_view(request):
    print("Rendering login.html from Django ✅")

    if request.method == 'POST':
        print("Form submitted:", request.POST)

    if request.method == 'POST' and request.POST.get('submit') == 'Login':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print("Trying login for:", email)

        user = authenticate(request, username=email, password=password)
        if user:
            print("✅ Login success")
            login(request, user)
            return redirect('dashboard')
        else:
            print("❌ Login failed")
            messages.error(request, 'Invalid email or password.')

    messages.warning(request, "⚠️ This is a test message — login page loaded.")
    return render(request, 'registration/login.html')

def get_crop_suggestion(crop):
    weeks = (date.today() - crop.date_planted).days // 7
    stage = crop.growth_stage
    suggestions = []

    if weeks < 2:
        suggestions.append("🟢 Ensure good soil moisture. Early germination stage.")
    elif stage == "vegetative":
        suggestions.append("🌱 Apply nitrogen-rich fertilizer.")
        suggestions.append("🧼 Watch for early pests like aphids.")
    elif stage == "flowering":
        suggestions.append("💧 Ensure consistent watering.")
        suggestions.append("🦟 Protect against fungal attacks.")
    elif stage == "harvest":
        suggestions.append("🌾 Prepare for harvest. Limit irrigation.")

    return {
        "weeks": weeks,
        "suggestions": suggestions
    }

@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    action = request.GET.get("action")
    show_form = action == "add"
    show_status = action == "status"
    show_weather = action == "weather"
    show_chatbot = action == "chatbot"
    show_upload = action == "upload"

    # Handle crop form POST
    if request.method == 'POST':
        name = request.POST.get('name')
        date_planted = request.POST.get('date')
        status = request.POST.get('status')
        land_area = request.POST.get('land_area')
        growth_stage = 'germination'
        Crop.objects.create(
            user=request.user,
            name=name,
            date_planted=date_planted,
            status=status,
            growth_stage=growth_stage,
            land_area=land_area
        )
        messages.success(request, "Crop added successfully!")
        return redirect('dashboard')

    crops = Crop.objects.filter(user=request.user)
    growing_crops = crops.filter(status="Growing")

    dashboard_data = []
    for crop in growing_crops:
        info = get_crop_suggestion(crop)
        dashboard_data.append({
            "crop": crop,
            "weeks": info["weeks"],
            "suggestions": info["suggestions"]
        })

    # 🌐 WEATHER: Call OpenWeatherMap API
    weather_data = None
    if show_weather:
        city = request.GET.get('city') or "Delhi"
        api_key = "YOUR_API_KEY"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url)
            data = response.json()
            if data.get("cod") == 200:
                weather_data = {
                    "city": data["name"],
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"]
                }
            else:
                print("Weather API error:", data.get("message"))
        except Exception as e:
            print("Weather API exception:", e)
    return render(request, 'dashboard.html', {
    'crops': crops,
    'growing_crops': growing_crops,
    'dashboard_data': dashboard_data,
    'profile': profile,
    'show_form': show_form,
    'show_status': show_status,
    'show_weather': show_weather,
    'weather_data': weather_data,
    'show_chatbot': show_chatbot,
    'show_upload': show_upload, 
    'action': action,           
})


@login_required
def add_crop(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        status = request.POST.get('status')

        Crop.objects.create(
            user=request.user,
            name=name,
            date_planted=date,
            status=status
        )
        return redirect('dashboard')

    return redirect('dashboard')




@csrf_exempt
def chatbot_reply(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '')

        try:
            genai.configure(api_key="YOUR_API_KEY")

            # ✅ Use a supported model from your list
            model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")
            response = model.generate_content(user_message)

            reply = response.text or "⚠️ Gemini did not return a reply."

        except Exception as e:
            reply = f"⚠️ Gemini API error: {str(e)}"

        return JsonResponse({'reply': reply})
@csrf_exempt
@login_required
def upload_crop_image(request):
    if request.method == 'POST' and request.FILES.get('crop_image'):
        crop_id = request.POST.get('crop_id')
        crop = Crop.objects.get(id=crop_id, user=request.user)

        image_file = request.FILES['crop_image']
        path = default_storage.save('uploads/' + image_file.name, image_file)
        image_url = default_storage.url(path)
        full_path = os.path.join(default_storage.location, path)

        try:
            pil_image = Image.open(full_path)

            genai.configure(api_key="AIzaSyCPx7fUInSQN-OQDVuJ1DNUSsHOTZu47DE")  # Replace with your key
            model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")


            response = model.generate_content([
                """
You are a smart agricultural assistant.

Analyze the uploaded crop image and provide the following details clearly:

1. 🔍 Crop Health Status: (Healthy / At Risk / Infected / Deficient)
2. ⚠️ Detected Issues
3. 💡 Suggestions for Improvement
4. 🧠 Reasoning

Use farmer-friendly, easy-to-understand language.
""",
                pil_image
            ])
            suggestions = response.text or "⚠️ No suggestions returned."

            # (Optional) Save to DB
            ImageAnalysis.objects.create(
                crop=crop,
                image=path,
                analysis_text=suggestions
            )

        except Exception as e:
            suggestions = f"❌ Error analyzing image: {str(e)}"

        # ✅ Render dashboard with AI results
        return render(request, 'dashboard.html', {
            'show_form': False,
            'show_status': False,
            'show_weather': False,
            'show_chatbot': False,
            'show_upload': True,
            'image_url': image_url,
            'suggestions': suggestions,
            'action': 'upload', 
        })

    return redirect('dashboard')
@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        user.first_name = request.POST.get('name')
        user.save()

        profile.age = request.POST.get('age')
        profile.profile_photo = request.POST.get('photo')
        profile.save()

        messages.success(request, "✅ Profile updated successfully!")
        return redirect('/dashboard?action=profile')
