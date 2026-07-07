import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useInterview } from "@/hooks/useInterview";
import { api } from "@/lib/api";
import { ArrowLeft, Sparkles, Briefcase, Code, Building2, Users, AlertTriangle } from "lucide-react";

export default function Setup() {
	const { user, isLoading } = useAuth();
	const [activeMode, setActiveMode] = useState<string>("resume");
	const [jdText, setJdText] = useState("");
	const [companyName, setCompanyName] = useState("EPAM");
	const [errorMsg, setErrorMsg] = useState<string | null>(null);
	const navigate = useNavigate();
	const { startInterview } = useInterview();

	// Check if current user has a parsed resume in the DB
	const { data: hasResume } = useQuery<boolean>({
		queryKey: ["resume-status"],
		queryFn: async () => {
			const res = await api.get("/auth/resume");
			return res.status === 200;
		},
		enabled: !!user,
	});

	const handleStartInterview = async () => {
		try {
			setErrorMsg(null);
			const session = await startInterview.mutateAsync({
				mode: activeMode,
				job_description: activeMode === "jd" ? jdText : undefined,
				company_name: activeMode === "company" ? companyName : undefined,
			});
			navigate(`/interview/${session.id}`);
		} catch (err: any) {
			setErrorMsg(err.message || "Failed to start interview session.");
		}
	};

	if (isLoading) {
		return (
			<div className="min-h-screen bg-slate-50 flex items-center justify-center">
				<div className="flex items-center gap-3">
					<span className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
					<span className="text-slate-600 font-medium">Loading session setup...</span>
				</div>
			</div>
		);
	}

	if (!user) {
		return (
			<div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center px-4">
				<div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm max-w-md w-full text-center flex flex-col gap-4">
					<h2 className="text-xl font-bold text-slate-900">Authentication Required</h2>
					<p className="text-slate-500 text-sm">Please log in to customize and start mock interview sessions.</p>
					<Link to="/login" className="w-full">
						<Button className="w-full bg-slate-900 text-white hover:bg-slate-800">Log In</Button>
					</Link>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
			<Header />

			<main className="flex-1 max-w-3xl mx-auto w-full px-4 py-12 flex flex-col gap-6">
				<div className="flex items-center gap-3">
					<Link to="/">
						<Button variant="ghost" size="sm" className="gap-1.5 text-slate-500 hover:text-slate-900">
							<ArrowLeft className="h-4 w-4" />
							Back to Dashboard
						</Button>
					</Link>
				</div>

				<div className="border-b border-slate-200 pb-5">
					<h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
						Customize Mock Session
					</h1>
					<p className="text-slate-500 mt-2">
						Configure your adaptive mock interview setup. The AI coordinator will select and focus topics matching your choice.
					</p>
				</div>

				{errorMsg && (
					<div className="p-4 text-sm text-red-700 rounded-xl bg-red-50 border border-red-200">
						{errorMsg}
					</div>
				)}

				<div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col gap-6">
					<div className="flex flex-col gap-3">
						<label className="text-xs font-bold text-slate-400 uppercase tracking-widest">
							Select Practice Mode
						</label>
						<div className="grid gap-3 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
							{[
								{ id: "resume", label: "Resume-Based", icon: Sparkles, desc: "Tailored to your parsed profile" },
								{ id: "jd", label: "Job Description", icon: Briefcase, desc: "Bridge matching a pasted role" },
								{ id: "company", label: "Company Simulator", icon: Building2, desc: "Simulate top company syllabus" },
								{ id: "coding", label: "Coding Concepts", icon: Code, desc: "Optimize complexity & paradigms" },
								{ id: "behavioral", label: "Behavioral Scenario", icon: Users, desc: "STAR framework & communication" },
							].map((tab) => {
								const Icon = tab.icon;
								const isActive = activeMode === tab.id;

								return (
									<button
										key={tab.id}
										type="button"
										onClick={() => {
											setActiveMode(tab.id);
											setErrorMsg(null);
										}}
										className={`p-4 rounded-xl border text-left flex flex-col gap-2 transition-all cursor-pointer ${
											isActive
												? "bg-slate-900 border-slate-900 text-white shadow-sm"
												: "bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700"
										}`}
									>
										<Icon className={`h-5 w-5 ${isActive ? "text-indigo-400" : "text-slate-500"}`} />
										<div>
											<span className="text-sm font-bold block">{tab.label}</span>
											<span className={`text-[10px] ${isActive ? "text-slate-300" : "text-slate-500"}`}>{tab.desc}</span>
										</div>
									</button>
								);
							})}
						</div>
					</div>

					{/* Custom inputs */}
					<div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 flex flex-col gap-3">
						{activeMode === "resume" && (
							<div className="flex flex-col gap-2">
								<h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
									<Sparkles className="h-4 w-4 text-indigo-600" />
									Resume-Based Mock Setup
								</h4>
								<p className="text-xs text-slate-500 leading-relaxed">
									Kira will tailor the entire syllabus and adaptive follow-up questions from the work experience, academic history, projects, and skills parsed directly from your uploaded resume.
								</p>
								{!hasResume && (
									<div className="mt-2 p-3 text-xs text-amber-900 rounded-lg bg-amber-50 border border-amber-200/60 flex items-start gap-2">
										<AlertTriangle className="h-4.5 w-4.5 text-amber-600 mt-0.5 flex-shrink-0" />
										<div>
											<p className="font-bold">No Resume Found</p>
											<p className="text-[10px] text-amber-700 mt-0.5">
												Please upload a resume on the dashboard first to practice using this mode.
											</p>
										</div>
									</div>
								)}
							</div>
						)}

						{activeMode === "jd" && (
							<div className="flex flex-col gap-3">
								<h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
									<Briefcase className="h-4 w-4 text-indigo-600" />
									Job Description Target
								</h4>
								<p className="text-xs text-slate-500 leading-relaxed">
									Paste the target job role details to customized and align target topics with specific technical qualifications.
								</p>
								<textarea
									className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 min-h-[140px] resize-none transition-all"
									placeholder="Paste details of the role or job description here..."
									value={jdText}
									onChange={(e) => setJdText(e.target.value)}
								/>
							</div>
						)}

						{activeMode === "company" && (
							<div className="flex flex-col gap-3">
								<h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
									<Building2 className="h-4 w-4 text-indigo-600" />
									Target Placement Preset
								</h4>
								<p className="text-xs text-slate-500 leading-relaxed">
									Select a placement structure matching syllabus layouts of popular recruiting pipelines.
								</p>
								<select
									className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 cursor-pointer"
									value={companyName}
									onChange={(e) => setCompanyName(e.target.value)}
								>
									<option value="EPAM">EPAM Simulator (Placeholder Preset)</option>
									<option value="Google">Google Simulator (Placeholder Preset)</option>
									<option value="Amazon">Amazon Simulator (Placeholder Preset)</option>
								</select>
							</div>
						)}

						{activeMode === "coding" && (
							<div className="flex flex-col gap-2">
								<h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
									<Code className="h-4 w-4 text-indigo-600" />
									Coding & Optimization mock
								</h4>
								<p className="text-xs text-slate-500 leading-relaxed">
									This mode evaluates programmatic optimization, predicting complexity boundaries, designing structures, and resolving common syntax exceptions.
								</p>
							</div>
						)}

						{activeMode === "behavioral" && (
							<div className="flex flex-col gap-2">
								<h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
									<Users className="h-4 w-4 text-indigo-600" />
									Behavioral mock
								</h4>
								<p className="text-xs text-slate-500 leading-relaxed">
									This mode evaluates communication structure using the STAR framework, resolution strategies for complex work deadlines, and collaboration patterns.
								</p>
							</div>
						)}
					</div>

					<Button
						className="w-full bg-indigo-600 text-white hover:bg-indigo-700 cursor-pointer h-11 text-sm font-semibold rounded-xl disabled:opacity-50 transition-all shadow-sm"
						onClick={handleStartInterview}
						disabled={
							startInterview.isPending ||
							(activeMode === "resume" && !hasResume) ||
							(activeMode === "jd" && !jdText.trim())
						}
					>
						{startInterview.isPending ? "Generating your custom interview session..." : "Start Mock Session"}
					</Button>
				</div>
			</main>
		</div>
	);
}
