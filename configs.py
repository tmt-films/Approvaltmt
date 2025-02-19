# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01


from os import path, getenv

class Config:
    API_ID = int(getenv("API_ID", "22980378"))
    API_HASH = getenv("API_HASH", "b4f6d14f1c852a965bf40d1d74d4368f")
    BOT_TOKEN = getenv("BOT_TOKEN", "7658007410:AAEBI0WpFdygVcMEBh5BiIwW3vdusQbiunY")
    # Your Force Subscribe Channel Id Below 
    CHID = int(getenv("CHID", "1001673745865")) # Make Bot Admin In This Channel
    # Admin Or Owner Id Below
    SUDO = list(map(int, getenv("SUDO", "7135894706").split()))
    MONGO_URI = getenv("MONGO_URI", "mongodb+srv://infogoatwork:TFH3tsED9xyGOgp9@cluster0.xvgt3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    
cfg = Config()

# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01
