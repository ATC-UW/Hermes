from supabase import create_client
from dotenv import load_dotenv
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

db = create_client(SUPABASE_URL, SUPABASE_KEY)
# print the tables in the database
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