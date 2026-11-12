import { NextRequest, NextResponse } from "next/server";
import { fallbackFromSupabase } from "@/lib/supabaseFallback";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint) {
    return NextResponse.json({ error: "Missing endpoint parameter" }, { status: 400 });
  }

  try {
    const data = await fallbackFromSupabase(endpoint);
    if (data !== null) {
      return NextResponse.json(data);
    }
    return NextResponse.json({ error: "Resource not found or database offline" }, { status: 404 });
  } catch (error: any) {
    return NextResponse.json({ error: error?.message || "Internal error" }, { status: 500 });
  }
}
