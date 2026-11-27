import Link from "next/link";
import type { ReactNode } from "react";

export default function AuthFrame({ children }: { children: ReactNode }) {
  return (
    <main className="rt-auth-grid">
      <section className="rt-auth-art" aria-label="RevoTask introduction">
        <Link href="/" className="relative z-10 flex w-fit items-center gap-3 font-semibold">
          <span className="flex size-10 rotate-3 items-center justify-center rounded-xl border-2 border-[#211621] bg-[#d9ff43] text-lg font-bold text-[#211621]">
            R
          </span>
          <span className="text-xl tracking-[-0.04em]">RevoTask</span>
        </Link>
        <div className="relative z-10 max-w-xl">
          <p className="mb-5 font-mono text-xs font-semibold uppercase tracking-[0.16em] text-[#d9ff43]">
            Organize less. Move more.
          </p>
          <p className="rt-display">
            Work has a
            <br />
            new rhythm.
          </p>
          <p className="mt-6 max-w-md text-base leading-relaxed text-[#e8dfca]">
            A focused space for teams who want clarity without the corporate beige.
          </p>
        </div>
        <p className="relative z-10 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c9b7ef]">
          Boards / Teams / Momentum
        </p>
      </section>
      <section className="rt-auth-form">{children}</section>
    </main>
  );
}
