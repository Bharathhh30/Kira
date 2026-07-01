import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/layout/Header";
import { SquigglyText } from "@/components/ui/squiggly-text";
import { EncryptedText } from "@/components/ui/encrypted-text";

export default function Landing() {
  const { user, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col font-sans">
      <Header />

      <main className="flex-1 flex flex-col justify-center items-center px-4 max-w-5xl mx-auto w-full py-12">
        {isLoading ? (
          <div className="flex items-center gap-3">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
            <span className="text-slate-500">Loading your profile...</span>
          </div>
        ) : user ? (
          /* Authenticated Dashboard view */
          <div className="w-full flex flex-col gap-8 animate-fade-in">
            <div className="border-b border-slate-200 pb-6">
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                <EncryptedText text={`Welcome to Interview Platform, ${user.name}!`} />
              </h1>
              <p className="text-slate-500 mt-2">
                Practice technical interviews adaptively and personalized for your next placement.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              <div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
                <span className="text-sm font-semibold text-slate-500">Completed Sessions</span>
                <span className="text-3xl font-bold text-slate-900">0</span>
              </div>
              <div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
                <span className="text-sm font-semibold text-slate-500">Average Performance</span>
                <span className="text-3xl font-bold text-slate-900">N/A</span>
              </div>
              <div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
                <span className="text-sm font-semibold text-slate-500">Target Focus Topics</span>
                <span className="text-sm text-slate-700">Data Structures, SQL, System Design</span>
              </div>
            </div>

            <div className="flex justify-center p-8 bg-slate-50 rounded-xl border border-slate-200">
              <div className="text-center flex flex-col gap-4 max-w-md items-center">
                <h3 className="text-lg font-semibold text-slate-900">Ready to start practicing?</h3>
                <p className="text-sm text-slate-500">
                  Choose your tech topics, upload your resume, and conduct a voice-interactive, adaptive mock interview.
                </p>
                <Button className="w-fit bg-slate-900 text-white hover:bg-slate-800" size="lg">
                  Start Practice Interview
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* Anonymous Hero Landing view */
          <div className="text-center flex flex-col items-center gap-6 max-w-2xl">
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 border border-slate-200 text-slate-600 uppercase tracking-widest">
              AI-Powered Mock Placement Prep
            </span>
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900">
              <SquigglyText className="font-extrabold text-slate-900">Adaptive  Technical Interviews by </SquigglyText><SquigglyText className="font-extrabold text-slate-900">Kira</SquigglyText>
            </h1>
            <p className="text-lg sm:text-xl text-slate-500">
              Simulate actual placement interviews with a responsive voice agent that asks follow-ups, tests coding logic, and helps you master your placement prep.
            </p>
            <div className="flex gap-4 mt-4 justify-center">
              <Link to="/login">
                <Button size="lg" className="px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-sm">
                  Get Started
                </Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="px-8 border-slate-200 hover:bg-slate-50 text-slate-900">
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
