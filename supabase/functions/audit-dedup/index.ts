// ============================================================
// LANGIT KOREA — Supabase Edge Function: audit_dedup
// ============================================================
// Deploy ke Supabase:
//   1. Buat folder: supabase/functions/audit-dedup/
//   2. Save sebagai: index.ts
//   3. Deploy: supabase functions deploy audit-dedup
// ============================================================
// Panggil via: curl https://[project].supabase.co/functions/v1/audit-dedup
//   -H "Authorization: Bearer [ANON_KEY]"
// ============================================================

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ── Konfigurasi ──
interface TableConfig {
  name: string;
  uniqueColumns: string[];
  label: string;
}

const TABLES: TableConfig[] = [
  {
    name: "soal_eps",
    uniqueColumns: ["sumber", "unit", "nomor_asli", "tipe"],
    label: "Soal EPS-TOPIK",
  },
  {
    name: "latihan_interaktif",
    uniqueColumns: ["unit", "seksi", "tipe_latihan", "urutan"],
    label: "Latihan Interaktif",
  },
  {
    name: "materi_unit",
    uniqueColumns: ["unit", "kategori", "sub"],
    label: "Materi Unit",
  },
  {
    name: "progress_unit",
    uniqueColumns: ["user_id", "unit_id", "seksi"],
    label: "Progress User",
  },
];

interface DuplicateGroup {
  key: string;
  count: number;
  ids: number[];
  created_at: string[];
}

interface AuditReport {
  generated_at: string;
  summary: {
    total_tables_checked: number;
    total_duplicate_groups: number;
    total_duplicate_rows: number;
  };
  details: {
    table: string;
    label: string;
    total_rows: number;
    duplicate_groups: number;
    duplicate_rows: number;
    percentage: number;
    groups: DuplicateGroup[];
  }[];
  recommendation: string;
}

serve(async (req: Request) => {
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_KEY") || "";

    if (!supabaseUrl || !supabaseKey) {
      return new Response(
        JSON.stringify({ error: "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY" }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseKey);
    const report: AuditReport = {
      generated_at: new Date().toISOString(),
      summary: {
        total_tables_checked: 0,
        total_duplicate_groups: 0,
        total_duplicate_rows: 0,
      },
      details: [],
      recommendation: "",
    };

    // Iterasi setiap tabel
    for (const table of TABLES) {
      report.summary.total_tables_checked++;

      // Ambil semua data
      const { data: allRows, error } = await supabase
        .from(table.name)
        .select("*")
        .order("created_at", { ascending: true });

      if (error) {
        console.error(`Error fetching ${table.name}:`, error);
        continue;
      }

      const totalRows = allRows?.length || 0;
      const columnPartition = table.uniqueColumns.join(",");

      // Gunakan Map untuk grup duplikat
      const groups = new Map<string, DuplicateGroup>();

      for (const row of allRows || []) {
        const key = table.uniqueColumns
          .map((col) => String((row as any)[col] ?? "NULL"))
          .join("||");

        if (!groups.has(key)) {
          groups.set(key, {
            key,
            count: 0,
            ids: [],
            created_at: [],
          });
        }
        const group = groups.get(key)!;
        group.count++;
        group.ids.push((row as any).id);
        group.created_at.push((row as any).created_at || "unknown");
      }

      // Filter hanya grup duplikat (count > 1)
      const duplicateGroups: DuplicateGroup[] = [];
      for (const [, group] of groups) {
        if (group.count > 1) {
          duplicateGroups.push(group);
        }
      }

      const duplicateRows = duplicateGroups.reduce(
        (sum, g) => sum + g.count,
        0
      );

      report.details.push({
        table: table.name,
        label: table.label,
        total_rows: totalRows,
        duplicate_groups: duplicateGroups.length,
        duplicate_rows: duplicateRows,
        percentage:
          totalRows > 0
            ? Math.round((duplicateRows / totalRows) * 100 * 100) / 100
            : 0,
        groups: duplicateGroups.slice(0, 20), // max 20 grup
      });

      report.summary.total_duplicate_groups += duplicateGroups.length;
      report.summary.total_duplicate_rows += duplicateRows;
    }

    // Rekomendasi
    if (report.summary.total_duplicate_rows > 0) {
      report.recommendation =
        `Ditemukan ${report.summary.total_duplicate_rows} baris duplikat ` +
        `di ${report.summary.total_duplicate_groups} grup. ` +
        `Jalankan langkah berikut:\n` +
        `1. Buka Supabase Dashboard > SQL Editor\n` +
        `2. Jalankan query di sql/dedup_detection.sql Bagian 2 (PREVIEW)\n` +
        `3. Jika sudah yakin, jalankan Bagian 3 (DELETE)\n` +
        `4. Jalankan Bagian 4 (UNIQUE CONSTRAINT) untuk cegah duplikat masa depan`;
    } else {
      report.recommendation = "✅ Tidak ada duplikat. Data sudah bersih.";
    }

    return new Response(JSON.stringify(report, null, 2), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    console.error("Fatal error:", err);
    return new Response(
      JSON.stringify({
        error: "Internal server error",
        message: err instanceof Error ? err.message : String(err),
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
