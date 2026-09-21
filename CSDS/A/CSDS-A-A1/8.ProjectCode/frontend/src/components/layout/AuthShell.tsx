import { BadgeCheck, FileSearch, Quote } from "lucide-react";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-teal-700 via-teal-800 to-slate-900 p-10 text-white lg:flex lg:flex-col">
        <div className="bg-grid absolute inset-0 opacity-20" />
        <div className="absolute -right-24 -top-24 size-96 rounded-full bg-teal-400/30 blur-3xl" />
        <Link to="/" className="relative">
          <span className="inline-flex items-center gap-2.5 [&_span]:text-white">
            <Logo className="[&_.text-primary]:text-teal-200" />
          </span>
        </Link>
        <div className="relative mt-auto max-w-md space-y-6">
          <Quote className="size-8 text-teal-200/80" />
          <p className="font-display text-2xl font-semibold leading-snug">
            “Is my cataract surgery covered?” should take seconds to answer - with the exact clause and page to prove it.
          </p>
          <ul className="space-y-3 text-sm text-teal-50/90">
            <li className="flex items-center gap-2">
              <FileSearch className="size-4 text-teal-200" /> Answers strictly from your own policy wording
            </li>
            <li className="flex items-center gap-2">
              <BadgeCheck className="size-4 text-teal-200" /> Every answer shows how well the cited text supports it
            </li>
          </ul>
        </div>
      </div>

      <div className="flex items-center justify-center px-4 py-10 sm:px-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-sm"
        >
          <Link to="/" className="mb-8 inline-block lg:hidden">
            <Logo />
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          <p className="mb-6 mt-1 text-sm text-muted-foreground">{subtitle}</p>
          {children}
        </motion.div>
      </div>
    </div>
  );
}
