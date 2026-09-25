import { Link } from "react-router-dom";
import { Shield, MapPinned, Mic, Radio, Camera, Sparkles } from "lucide-react";

const FEATURES = [
  { icon: MapPinned, title: "Safe Route", text: "Routes scored by area risk and time of day." },
  { icon: Mic, title: "SafePhrase", text: "A spoken phrase or one tap starts an emergency." },
  { icon: Radio, title: "Live tracking", text: "Guardians watch your location move in real time." },
  { icon: Camera, title: "Evidence capture", text: "Photo or audio, hashed and time-stamped." },
  { icon: Sparkles, title: "AI assistant", text: "Gemini-powered safety guidance, anytime." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <div className="flex-1 max-w-3xl mx-auto w-full px-6 py-16 text-center">
        <div className="flex justify-center mb-6">
          <div className="bg-brand-600/20 border border-brand-600 rounded-2xl p-4">
            <Shield size={40} className="text-brand-400" />
          </div>
        </div>
        <h1 className="text-4xl font-bold mb-3">SHEGUARD</h1>
        <p className="text-slate-400 mb-8">
          A women's safety companion: safer routes, hands-free help, live guardian tracking
          and secure evidence, in one app.
        </p>
        <div className="flex gap-3 justify-center mb-14">
          <Link to="/register" className="bg-brand-600 hover:bg-brand-700 px-6 py-3 rounded-xl font-medium">
            Get started
          </Link>
          <Link to="/login" className="border border-slate-700 hover:border-brand-500 px-6 py-3 rounded-xl font-medium">
            Log in
          </Link>
        </div>

        <div className="grid sm:grid-cols-2 gap-4 text-left">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex gap-3">
              <Icon size={22} className="text-brand-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-medium">{title}</div>
                <div className="text-sm text-slate-400">{text}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <footer className="text-center text-xs text-slate-600 pb-6">
        In an active emergency, always contact local emergency services first.
      </footer>
    </div>
  );
}
