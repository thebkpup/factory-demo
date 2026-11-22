// clear524 probe a sqli — measurement fixture, not production code
import { db } from "../lib/db";

export async function findUserByName(name: string): Promise<unknown> {
  const q = "SELECT id, email, role FROM users WHERE name = '" + name + "'";
  return db.query(q);
}
