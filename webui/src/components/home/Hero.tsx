import { HeroIllustration } from "../ui/Illustrations"

export function Hero() {
  return (
    <section className="flex flex-col items-center">
      <HeroIllustration />
      <h1 className="mt-6 text-center text-3xl sm:text-4xl md:text-5xl font-semibold text-neutral-900 tracking-tight">
        我能为您做什么？
      </h1>
    </section>
  )
}
