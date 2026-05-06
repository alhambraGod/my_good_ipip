import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="bg-navy-text text-saffron-100/90 py-12 px-6">
      <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-sm">
        <div className="col-span-2">
          <div className="text-saffron-100 font-black text-lg flex items-center gap-2">
            <span>🪔</span> CareerDNA India
          </div>
          <p className="mt-2 max-w-md text-saffron-100/85 leading-relaxed">
            Holland RIASEC + Big Five (OCEAN). Built for Indian Gen-Z reality.
            Not a clinical assessment — used to spark direction, not replace
            therapy.
          </p>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-saffron-100/75 mb-2 font-semibold">
            Product
          </div>
          <ul className="space-y-1">
            <li>
              <Link href="/test" className="hover:text-saffron-100">
                Take the test
              </Link>
            </li>
            <li>
              <Link href="/archetypes" className="hover:text-saffron-100">
                All 24 archetypes
              </Link>
            </li>
            <li>
              <Link href="/dashboard" className="hover:text-saffron-100">
                My results
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-saffron-100/75 mb-2 font-semibold">
            About
          </div>
          <ul className="space-y-1">
            <li>
              <Link href="/#science" className="hover:text-saffron-100">
                The science
              </Link>
            </li>
            <li>
              <Link href="/#faq" className="hover:text-saffron-100">
                FAQ
              </Link>
            </li>
            <li>
              <Link href="/#privacy" className="hover:text-saffron-100">
                Privacy
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="max-w-6xl mx-auto mt-8 pt-6 border-t border-white/10 text-xs text-saffron-100/75 flex flex-col sm:flex-row gap-2 justify-between">
        <p>&copy; 2026 CareerDNA India · For Indian Gen-Z, by Indians.</p>
        <p>Built on IPIP-NEO Big Five + Holland RIASEC personality science.</p>
      </div>
    </footer>
  );
}
