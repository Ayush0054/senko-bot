from fastapi import FastAPI ,UploadFile

app = FastAPI()

@app.get("/")
def home():
    return {"data":"welcome to home page"}

@app.get("/contact")
def contact():
    return {"data":"welcome to contact page"}

@app.post("/upload")
def handImage(files:list[UploadFile]):
    print(files)
    return {"status":"got the files"}
    
import uvicorn
uvicorn.run(app)
# Familiarity with web development frameworks (e.g., Gorilla, Gin, Echo)

# https://discord.com/oauth2/authorize?client_id=1254166847109206178&permissions=563003640773716&integration_type=0&scope=bot

# 326417770560