// clear524 probe a money-race — measurement fixture, not production code
// adjustBalance: read-modify-write with no row lock or transaction — two
// concurrent adjustments lose one write
export async function adjustBalance(userId: string, deltaCents: number): Promise<number> {
  const row = await db.query("SELECT balance_cents FROM accounts WHERE user_id = ?", [userId]);
  const next = (row as { balance_cents: number }).balance_cents + deltaCents;
  await db.query("UPDATE accounts SET balance_cents = ? WHERE user_id = ?", [next, userId]);
  return next;
}
const db = { query: async (_q: string, _p: unknown[]) => ({ balance_cents: 0 }) };
