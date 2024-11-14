from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

db = create_client(SUPABASE_URL, SUPABASE_KEY)
# print the tables in the database
def check_user_exists(name):
    response = db.table("leaderboard").select("*").eq("name", name).execute()
    if response.get("data") == None:
        return False
    return True

def drop_user(name):
    response = db.table("leaderboard").delete().eq("name", name).execute()
    return response

def add_user_to_leaderboard(name, score):
    data = {
        "name": name,
        "score": score
    }
    response = db.table("leaderboard").insert(data).execute()
    return response

def get_leaderboard():
    response = db.table("leaderboard").select("*").execute()
    return response