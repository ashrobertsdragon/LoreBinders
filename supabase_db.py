import os

from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Dict, Any


load_dotenv()

class SupabaseDatabase:
  def __init__(self):
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    self.supabase: Client = create_client(url, key)

  def read_data(self, table: str, fields: List[str]) -> List[Dict[str, Any]]:
    return self.supabase.table(table).select(", ".join(fields)).execute().data

  def update_data(self, table: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> None:
    query = self.supabase.table(table)
    for key, value in conditions.items():
      query = query.eq(key, value)
    query.update(data).execute()

  def insert_data(self, table: str, data: Dict[str, Any]) -> None:
    self.supabase.table(table).insert(data).execute()

  def check_existing(self, table: str, criteria: Dict[str, Any]) -> bool:
    query = self.supabase.table(table).select("id")
    for key, value in criteria.items():
      query = query.filter(key, 'eq', value)
    result = query.execute().data
    return len(result) > 0
