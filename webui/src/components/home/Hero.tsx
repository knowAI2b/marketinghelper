import { HeroIllustration } from "../ui/Illustrations"

export function Hero() {
  return (
    <section className="flex flex-col items-center relative">
      <div className="absolute inset-0 -z-10 h-[320px] mx-auto max-w-4xl top-0 bg-gradient-to-b from-[var(--color-surface)] to-transparent" aria-hidden />
      <HeroIllustration />
      <h1 className="mt-8 text-center text-3xl sm:text-4xl md:text-5xl font-semibold text-[var(--color-text)] tracking-tight leading-tight">
        我能为您做什么？
      </h1>
    </section>
  )
}
