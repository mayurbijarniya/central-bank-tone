import "server-only"

import { readFile } from "node:fs/promises"
import path from "node:path"
import { cache } from "react"

import type { Bank, BankDetail, GlobalPoint, Summary } from "@/lib/types"

const DATA_DIR = path.join(process.cwd(), "public", "data")

async function read<T>(file: string): Promise<T> {
  return JSON.parse(await readFile(path.join(DATA_DIR, file), "utf8")) as T
}

export const getSummary = cache(() => read<Summary>("summary.json"))
export const getGlobalTone = cache(() => read<GlobalPoint[]>("global.json"))
export const getBanks = cache(() => read<Bank[]>("banks.json"))
export const getBank = cache((code: string) => read<BankDetail>(`banks/${code}.json`))
