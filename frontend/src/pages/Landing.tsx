import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { EncryptedText } from "@/components/ui/encrypted-text";
import { SquigglyText } from "@/components/ui/squiggly-text";
import { useAuth } from "@/hooks/useAuth";
import { useInterview } from "@/hooks/useInterview";
import { api } from "@/lib/api";

export default function Landing() {
	const { user, isLoading } = useAuth();
	const [isUploading, setIsUploading] = useState(false);
	const [uploadMessage, setUploadMessage] = useState<string | null>(null);
	const [uploadError, setUploadError] = useState<string | null>(null);
	const [activeMode, setActiveMode] = useState<string>("resume");
	const [jdText, setJdText] = useState("");
	const [companyName, setCompanyName] = useState("EPAM");
	const navigate = useNavigate();
	const { startInterview } = useInterview();

	const handleStartInterview = async () => {
		try {
			const session = await startInterview.mutateAsync({
				mode: activeMode,
				job_description: activeMode === "jd" ? jdText : undefined,
				company_name: activeMode === "company" ? companyName : undefined,
			});
			navigate(`/interview/${session.id}`);
		} catch (err: any) {
			setUploadError(err.message || "Failed to start interview session.");
		}
	};

	// Check if current user has a parsed resume in the DB
	const { data: hasResume, refetch: refetchResumeStatus } = useQuery<boolean>({
		queryKey: ["resume-status"],
		queryFn: async () => {
			const res = await api.get("/auth/resume");
			return res.status === 200; // true if resume exists, false if 404
		},
		enabled: !!user,
	});

	const handleFileChange = async (
		event: React.ChangeEvent<HTMLInputElement>,
	) => {
		const file = event.target.files?.[0];
		if (!file) return;

		if (!file.name.toLowerCase().endsWith(".pdf")) {
			setUploadError("Only PDF files are supported.");
			return;
		}

		setIsUploading(true);
		setUploadError(null);
		setUploadMessage(null);

		const formData = new FormData();
		formData.append("file", file);

		try {
			const res = await api.post("/auth/resume", undefined, { body: formData });
			if (!res.ok) {
				const errData = await res.json();
				throw new Error(errData.detail || "Failed to upload resume.");
			}
			setUploadMessage(
				"Resume upload accepted! We are parsing your profile in the background. Check your Profile page in a few seconds.",
			);
			// Wait a moment and check status again
			setTimeout(() => {
				refetchResumeStatus();
			}, 4000);
		} catch (err: any) {
			setUploadError(err.message || "An error occurred during upload.");
		} finally {
			setIsUploading(false);
		}
	};

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
								<EncryptedText
									text={`Welcome to Interview Platform, ${user.name}!`}
								/>
							</h1>
							<p className="text-slate-500 mt-2">
								Practice technical interviews adaptively and personalized for
								your next placement.
							</p>
						</div>

						<div className="grid gap-6 md:grid-cols-3">
							<div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
								<span className="text-sm font-semibold text-slate-500">
									Completed Sessions
								</span>
								<span className="text-3xl font-bold text-slate-900">0</span>
							</div>
							<div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
								<span className="text-sm font-semibold text-slate-500">
									Average Performance
								</span>
								<span className="text-3xl font-bold text-slate-900">N/A</span>
							</div>
							<div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2">
								<span className="text-sm font-semibold text-slate-500">
									Target Focus Topics
								</span>
								<span className="text-sm text-slate-700">
									Data Structures, SQL, System Design
								</span>
							</div>
						</div>

						<div className="grid gap-6 md:grid-cols-2 mt-2">
							{/* Card 1: Resume Upload / Status */}
							<div className="p-6 bg-slate-50 rounded-xl border border-slate-200 flex flex-col justify-between gap-4">
								<div className="flex flex-col gap-2">
									<h3 className="text-lg font-bold text-slate-900">
										AI Profile Parser
									</h3>
									{hasResume ? (
										<p className="text-sm text-slate-500 leading-relaxed">
											✓ Your resume has been parsed successfully! We have
											automatically loaded your skills, experiences, projects,
											and coding ratings into your Profile.
										</p>
									) : (
										<p className="text-sm text-slate-500 leading-relaxed">
											Upload your technical resume to auto-generate a structured
											profile. Our parser extracts your work history, projects,
											and coding ratings to customize your AI mock interviews.
										</p>
									)}
								</div>

								<div className="flex flex-col gap-3">
									{uploadError && (
										<div className="p-3 text-xs text-red-700 rounded-lg bg-red-50 border border-red-200">
											{uploadError}
										</div>
									)}
									{uploadMessage && (
										<div className="p-3 text-xs text-slate-800 rounded-lg bg-slate-100 border border-slate-200">
											{uploadMessage}
										</div>
									)}

									<div className="flex items-center gap-3">
										{hasResume ? (
											<>
												<Link to="/profile">
													<Button
														className="bg-slate-900 text-white hover:bg-slate-800"
														size="sm"
													>
														View Profile
													</Button>
												</Link>
												<label htmlFor="resume-file-input">
													<input
														type="file"
														id="resume-file-input"
														className="hidden"
														accept=".pdf"
														onChange={handleFileChange}
														disabled={isUploading}
													/>
													<Button
														asChild
														variant="outline"
														size="sm"
														className="border-slate-300 hover:bg-slate-100 cursor-pointer"
													>
														<span>Update Resume</span>
													</Button>
												</label>
											</>
										) : (
											<label htmlFor="resume-file-input">
												<input
													type="file"
													id="resume-file-input"
													className="hidden"
													accept=".pdf"
													onChange={handleFileChange}
													disabled={isUploading}
												/>
												<Button
													asChild
													className="bg-slate-900 text-white hover:bg-slate-800 cursor-pointer"
													size="sm"
												>
													<span>
														{isUploading
															? "Uploading & Parsing..."
															: "Upload Resume (PDF)"}
													</span>
												</Button>
											</label>
										)}
										{isUploading && (
											<span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-transparent" />
										)}
									</div>
								</div>
							</div>

							{/* Card 2: Practice Interview */}
							<div className="p-6 bg-slate-50 rounded-xl border border-slate-200 flex flex-col justify-between gap-6 md:col-span-1">
								<div className="flex flex-col gap-3">
									<h3 className="text-lg font-bold text-slate-900">
										Mock Interview Customizer
									</h3>
									<p className="text-xs text-slate-500 leading-normal">
										Select a practicing mode to customize your adaptive syllabus and start your session.
									</p>

									{/* Custom tabs */}
									<div className="flex flex-wrap gap-1.5 mt-2">
										{[
											{ id: "resume", label: "Resume-Based" },
											{ id: "jd", label: "Job Description" },
											{ id: "company", label: "Company Simulator" },
											{ id: "coding", label: "Coding Concepts" },
											{ id: "behavioral", label: "Behavioral Scenario" },
										].map((tab) => (
											<button
												key={tab.id}
												type="button"
												onClick={() => {
													setActiveMode(tab.id);
												}}
												className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold cursor-pointer border transition-all ${
													activeMode === tab.id
														? "bg-slate-900 text-white border-slate-900 shadow-sm"
														: "bg-white text-slate-600 border-slate-250 hover:bg-slate-100"
												}`}
											>
												{tab.label}
											</button>
										))}
									</div>

									{/* Tab content panel */}
									<div className="mt-3 bg-white border border-slate-200/80 rounded-xl p-3.5 min-h-[140px] flex flex-col justify-center">
										{activeMode === "resume" && (
											<div className="flex flex-col gap-1.5">
												<span className="text-xs font-semibold text-slate-800">Resume-Based mock</span>
												<p className="text-[11px] text-slate-500 leading-relaxed">
													Tailored to your uploaded profile. Questions are dynamically generated from your skills, experience, and projects.
												</p>
												{!hasResume && (
													<span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200/60 rounded px-2 py-0.5 w-fit mt-1">
														Requires resume upload first
													</span>
												)}
											</div>
										)}

										{activeMode === "jd" && (
											<div className="flex flex-col gap-2">
												<span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
													Target Job Description
												</span>
												<textarea
													className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-300 min-h-[90px] resize-none"
													placeholder="Paste details of the role to generate custom syllabus topics..."
													value={jdText}
													onChange={(e) => setJdText(e.target.value)}
												/>
											</div>
										)}

										{activeMode === "company" && (
											<div className="flex flex-col gap-2">
												<span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
													Target Company Preset (Simulator MVP Placeholder)
												</span>
												<select
													className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-xs text-slate-800 focus:outline-none focus:border-slate-300"
													value={companyName}
													onChange={(e) => setCompanyName(e.target.value)}
												>
													<option value="EPAM">EPAM Simulator (Placeholder Preset)</option>
													<option value="Google">Google Simulator (Placeholder Preset)</option>
													<option value="Amazon">Amazon Simulator (Placeholder Preset)</option>
												</select>
												<span className="text-[10px] text-slate-400 leading-normal">
													Select a preset matching top placement syllabus structures.
												</span>
											</div>
										)}

										{activeMode === "coding" && (
											<div className="flex flex-col gap-1">
												<span className="text-xs font-semibold text-slate-800">Coding mock</span>
												<p className="text-[11px] text-slate-500 leading-relaxed">
													Practice algorithmic complexities, choosing data structures, code optimizations, and design paradigms.
												</p>
											</div>
										)}

										{activeMode === "behavioral" && (
											<div className="flex flex-col gap-1">
												<span className="text-xs font-semibold text-slate-800">Behavioral mock</span>
												<p className="text-[11px] text-slate-500 leading-relaxed">
													Practice STAR leadership framework, project communication, deadlines, and team collaboration.
												</p>
											</div>
										)}
									</div>
								</div>
								<div>
									<Button
										className="w-full bg-slate-900 text-white hover:bg-slate-800 cursor-pointer disabled:opacity-50"
										size="sm"
										onClick={handleStartInterview}
										disabled={
											startInterview.isPending || 
											(activeMode === "resume" && !hasResume) ||
											(activeMode === "jd" && !jdText.trim())
										}
									>
										{startInterview.isPending
											? "Generating session..."
											: "Start Mock Session"}
									</Button>
								</div>
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
							<SquigglyText className="font-extrabold text-slate-900">
								Adaptive Technical Interviews by{" "}
							</SquigglyText>
							<SquigglyText className="font-extrabold text-slate-900">
								Kira
							</SquigglyText>
						</h1>
						<p className="text-lg sm:text-xl text-slate-500">
							Simulate actual placement interviews with a responsive voice agent
							that asks follow-ups, tests coding logic, and helps you master
							your placement prep.
						</p>
						<div className="flex gap-4 mt-4 justify-center">
							<Link to="/login">
								<Button
									size="lg"
									className="px-8 bg-slate-900 text-white hover:bg-slate-800 shadow-sm"
								>
									Get Started
								</Button>
							</Link>
							<Link to="/register">
								<Button
									size="lg"
									variant="outline"
									className="px-8 border-slate-200 hover:bg-slate-50 text-slate-900"
								>
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
