import { NextResponse } from 'next/server';
import fs from 'fs/promises';

export async function GET() {
  try {
    const baselinePath = "/Users/rakhahub/Documents/Kuliah/Semester 2/Information Retriveal/Tugas Crawling/Tugas IR/Tugas Final/data/output/hasil_siswa_berprestasi.json";
    const evaluationPath = "/Users/rakhahub/Documents/Kuliah/Semester 2/Information Retriveal/Tugas Crawling/Tugas IR/Tugas Jurnal/data/evaluation_results.json";

    const baselineRaw = await fs.readFile(baselinePath, 'utf-8');
    const evaluationRaw = await fs.readFile(evaluationPath, 'utf-8');

    return NextResponse.json({
      baseline: JSON.parse(baselineRaw),
      evaluation: JSON.parse(evaluationRaw),
    });
  } catch (error) {
    console.error("Error loading dashboard data:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
