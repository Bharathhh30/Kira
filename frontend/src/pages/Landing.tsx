import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/layout/Header";

export default function Landing() {
  const { user, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Header />

      <main className="flex-1 flex flex-col justify-center items-center px-4 max-w-5xl mx-auto w-full py-12">
        {isLoading ? (
          <div className="flex items-center gap-3">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            <span className="text-slate-400">Loading your profile...</span>
          </div>
        ) : user ? (
          /* Authenticated Dashboard view */
          <div className="w-full flex flex-col gap-8 animate-fade-in">
            <div className="border-b border-white/10 pb-6">
              <h1 className="text-3xl font-bold tracking-tight">
                Welcome to Interview Platform,{" "}
                <span className="bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                  {user.name}
                </span>
                !
              </h1>
              <p className="text-slate-400 mt-2">
                Practice technical interviews adaptively and personalized for your next placement.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              <div className="p-6 rounded-lg bg-white/5 border border-white/10 flex flex-col gap-2">
                <span className="text-sm font-semibold text-slate-400">Completed Sessions</span>
                <span className="text-3xl font-bold text-white">0</span>
              </div>
              <div className="p-6 rounded-lg bg-white/5 border border-white/10 flex flex-col gap-2">
                <span className="text-sm font-semibold text-slate-400">Average Performance</span>
                <span className="text-3xl font-bold text-white">N/A</span>
              </div>
              <div className="p-6 rounded-lg bg-white/5 border border-white/10 flex flex-col gap-2">
                <span className="text-sm font-semibold text-slate-400">Target Focus Topics</span>
                <span className="text-sm text-slate-300">Data Structures, SQL, System Design</span>
              </div>
            </div>

            <div className="flex justify-center p-8 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-xl border border-blue-500/20">
              <div className="text-center flex flex-col gap-4 max-w-md items-center">
                <h3 className="text-lg font-semibold">Ready to start practicing?</h3>
                <p className="text-sm text-slate-400">
                  Choose your tech topics, upload your resume, and conduct a voice-interactive, adaptive mock interview.
                </p>
                <Button className="w-fit" size="lg">
                  Start Practice Interview
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* Anonymous Hero Landing view */
          <div className="text-center flex flex-col items-center gap-6 max-w-2xl">
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 uppercase tracking-widest">
              AI-Powered Mock Placement Prep
            </span>
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Adaptive Technical Interviews by <span className="bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">Kira</span>
            </h1>
            <p className="text-lg sm:text-xl text-slate-400">
              Simulate actual placement interviews with a responsive voice agent that asks follow-ups, tests coding logic, and helps you master your placement prep.
            </p>
            <div className="flex gap-4 mt-4 justify-center">
              <Link to="/login">
                <Button size="lg" className="px-8 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/35">
                  Get Started
                </Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="px-8 border-white/10 hover:bg-white/5">
                  Create Account
                </Button>
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
