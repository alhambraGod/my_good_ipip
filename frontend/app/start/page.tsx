import Link from "next/link";

export default function StartPage() {
  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full">
        <div className="bg-white rounded-3xl shadow-xl p-8 md:p-10 border border-slate-100">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold gradient-text mb-2">MindIQ</h1>
            <p className="text-slate-500 text-sm">
              Personality Assessment
            </p>
          </div>

          <h2 className="text-2xl font-bold text-slate-800 mb-6 text-center">
            Get Ready to Begin
          </h2>

          <div className="space-y-4 mb-8">
            {[
              {
                icon: "&#9201;",
                title: "40 questions, ~5 minutes",
                desc: "Quick questions about your personality preferences and behaviors.",
              },
              {
                icon: "&#10003;",
                title: "No right or wrong answers",
                desc: "Just answer honestly — the more authentic you are, the better your results.",
              },
              {
                icon: "&#9740;",
                title: "Your data is private & secure",
                desc: "We respect your privacy. Your responses are encrypted and confidential.",
              },
            ].map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-4 bg-slate-50 rounded-xl p-4"
              >
                <div
                  className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center flex-shrink-0 text-lg font-bold"
                  dangerouslySetInnerHTML={{ __html: item.icon }}
                />
                <div>
                  <h3 className="font-semibold text-slate-800">
                    {item.title}
                  </h3>
                  <p className="text-sm text-slate-500 mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <Link
            href="/profile"
            className="block w-full bg-indigo-600 text-white font-bold text-lg py-4 rounded-2xl hover:bg-indigo-700 transition-colors shadow-lg text-center"
          >
            Begin Assessment
          </Link>

          <Link
            href="/"
            className="block text-center mt-4 text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            &larr; Back to home
          </Link>
        </div>
      </div>
    </main>
  );
}
