import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { EncryptedText } from "@/components/ui/encrypted-text";
import { SquigglyText } from "@/components/ui/squiggly-text";
import { useAuth } from "@/hooks/useAuth";
import { useInterviews } from "@/hooks/useInterview";
import { api } from "@/lib/api";

export default function Landing() {
	const { user, isLoading } = useAuth();
	const [isUploading, setIsUploading] = useState(false);
	const [uploadMessage, setUploadMessage] = useState<string | null>(null);
	const [uploadError, setUploadError] = useState<string | null>(null);
	const { data: interviews } = useInterviews();

	const completedCount = interviews ? interviews.filter((i) => i.is_completed).length : 0;

	let avgPerfStr = "N/A";
	if (interviews) {
		const completedInterviews = interviews.filter(
			(i) => i.is_completed && i.report && i.report.granular_averages
		);
		if (completedInterviews.length > 0) {
			let totalSum = 0;
			for (const i of completedInterviews) {
				const report = i.report!;
				const score = (
					(report.granular_averages.communication +
						report.granular_averages.accuracy +
						report.granular_averages.confidence +
						report.granular_averages.completeness) / 4
				) * 100;
				totalSum += score;
			}
			avgPerfStr = `${Math.round(totalSum / completedInterviews.length)}%`;
		}
	}

	const latestInterview = interviews && interviews.length > 0 ? interviews[0] : null;
	const targetTopics = latestInterview && (latestInterview.current_topic || latestInterview.remaining_topics.length > 0)
		? [latestInterview.current_topic, ...latestInterview.remaining_topics].filter(Boolean).slice(0, 3).join(", ")
		: "Data Structures, SQL, System Design";

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
							<div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col justify-between gap-2 min-h-[110px]">
								<div className="flex flex-col gap-1">
									<span className="text-sm font-semibold text-slate-500">
										Completed Sessions
									</span>
									<span className="text-3xl font-bold text-slate-900">{completedCount}</span>
								</div>
								{interviews && interviews.length > 0 && (
									<Link
										to="/history"
										className="text-xs font-bold text-black hover:text-green-800 transition-colors flex items-center gap-1"
									>
										View History &rarr;
									</Link>
								)}
							</div>
							<div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2 min-h-[110px]">
								<span className="text-sm font-semibold text-slate-500">
									Average Performance
								</span>
								<span className="text-3xl font-bold text-slate-900">{avgPerfStr}</span>
							</div>
							<div className="p-6 rounded-lg bg-slate-50 border border-slate-200 flex flex-col gap-2 min-h-[110px]">
								<span className="text-sm font-semibold text-slate-500">
									Target Focus Topics
								</span>
								<span className="text-sm text-slate-700 font-medium line-clamp-2">
									{targetTopics}
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
										Mock Interview Session
									</h3>
									<p className="text-xs text-slate-500 leading-relaxed">
										Practice algorithmic complexities, choosing data structures, STAR behavioral frameworks, and optimize code logic in real time with our adaptive AI voice agent.
									</p>
								</div>
								<div>
									<Link to="/setup" className="w-full inline-block">
										<Button
											className="w-full bg-slate-900 text-white hover:bg-slate-800 cursor-pointer text-sm font-semibold rounded-xl py-5 transition-all shadow-sm"
										>
											Start Mock Session
										</Button>
									</Link>
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
