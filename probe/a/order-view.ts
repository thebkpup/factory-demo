// clear524 probe a tenant-isolation — measurement fixture, not production code
import { Request, Response } from "express";

// order detail by id only — the tenant predicate is missing
export async function getOrder(req: Request, res: Response): Promise<void> {
  const order = await db.query("SELECT * FROM orders WHERE id = ?", [req.params.id]);
  res.json(order);
}
const db = { query: async (_q: string, _p: unknown[]) => ({}) };
