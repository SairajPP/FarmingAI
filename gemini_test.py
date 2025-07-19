import google.generativeai as genai

genai.configure(api_key="AIzaSyCPx7fUInSQN-OQDVuJ1DNUSsHOTZu47DE")

models = genai.list_models()

for m in models:
    print(m.name)
