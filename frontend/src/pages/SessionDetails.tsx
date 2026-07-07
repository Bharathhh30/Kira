import { Link, useParams } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { useInterview } from "@/hooks/useInterview";
import { ArrowLeft, Calendar, Clock, Award, CheckCircle, AlertTriangle, HelpCircle, User, BookOpen } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const renderQuestionTextAndCode = (qText: string) => {
	const hasSnippet = qText.includes("|||");
	const parts = qText.split("|||");
	const question = parts[0]?.trim() || qText;
	const code = hasSnippet ? parts.slice(1).join("|||").trim() : "";

	return (
		<div className="flex flex-col gap-3 w-full">
			<p className="whitespace-pre-wrap">{question}</p>
			{code && (
				<pre className="text-slate-100 font-mono text-[11px] leading-relaxed whitespace-pre overflow-auto p-4 bg-slate-950 rounded-xl border border-slate-800 text-left">
					{code}
				</pre>
			)}
		</div>
	);
};

export default function SessionDetails() {
	const { id } = useParams<{ id: string }>();
	const { interview: session, isLoading, error } = useInterview(id);

	const formatDate = (dateStr: string) => {
		const d = new Date(dateStr);
		return d.toLocaleDateString("en-US", {
			month: "short",
			day: "numeric",
			year: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	};

	const getScore = (report: any) => {
		if (!report || !report.granular_averages) return null;
		const { communication, accuracy, confidence, completeness } = report.granular_averages;
		return Math.round(((communication + accuracy + confidence + completeness) / 4) * 100);
	};

	// Format chart data for progression graph
	const getChartData = () => {
		if (!session || !session.history) return [];
		return session.history
			.map((entry, index) => {
				let scoreVal = entry.score !== undefined && entry.score !== null ? entry.score : null;
				if (scoreVal === null && entry.granular_scores) {
					scoreVal = (
						entry.granular_scores.communication +
						entry.granular_scores.accuracy +
						entry.granular_scores.confidence +
						entry.granular_scores.completeness
					) / 4;
				}
				return {
					name: `Q${index + 1}`,
					score: scoreVal !== null ? Math.round(scoreVal * 100) : null,
				};
			})
			.filter((item) => item.score !== null);
	};

	const chartData = getChartData();
	const overallScore = session ? getScore(session.report) : null;

	return (
		<div className="min-h-screen bg-white text-slate-900 flex flex-col font-sans">
			<Header />

			<main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
				<div className="flex items-center gap-3 mb-6">
					<Link to="/history">
						<Button variant="ghost" size="sm" className="gap-1.5 text-slate-500 hover:text-slate-900">
							<ArrowLeft className="h-4 w-4" />
							History
						</Button>
					</Link>
				</div>

				{isLoading ? (
					<div className="flex flex-col items-center justify-center py-12 gap-3">
						<span className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
						<span className="text-sm text-slate-500">Loading details...</span>
					</div>
				) : error ? (
					<div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
						Failed to load interview details: {error.message}
					</div>
				) : !session ? (
					<div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-sm text-center">
						Interview session not found.
					</div>
				) : (
					<div className="flex flex-col gap-8">
						{/* Header Panel */}
						<div className="border-b border-slate-200 pb-5">
							<div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
								<div>
									<div className="flex items-center gap-2 flex-wrap">
										<h1 className="text-3xl font-bold tracking-tight text-slate-900 capitalize">
											{session.current_topic || "Topic Selection"} Mock
										</h1>
										<span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 border border-slate-200">
											{session.interview_mode === "jd" ? "Job Desc" : session.interview_mode}
										</span>
										{session.is_completed ? (
											<span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-50 text-green-700 border border-green-200/50">
												Completed
											</span>
										) : (
											<span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/50">
												In Progress
											</span>
										)}
									</div>
									<div className="flex items-center gap-4 text-xs text-slate-500 mt-2 flex-wrap">
										<span className="flex items-center gap-1">
											<Calendar className="h-3.5 w-3.5" />
											{formatDate(session.created_at)}
										</span>
										<span className="flex items-center gap-1">
											<Clock className="h-3.5 w-3.5" />
											{Math.floor((1800 - session.remaining_time) / 60)}m elapsed
										</span>
									</div>
								</div>

								{/* Overall Score Badge */}
								{overallScore !== null && (
									<div className="flex items-center gap-3 bg-indigo-50 border border-indigo-100 p-4 rounded-xl">
										<Award className="h-8 w-8 text-indigo-600" />
										<div>
											<p className="text-[10px] text-indigo-500 font-bold uppercase tracking-wider leading-none">
												Overall Score
											</p>
											<p className="text-2xl font-bold text-slate-950 mt-1 leading-none">
												{overallScore}%
											</p>
										</div>
									</div>
								)}
							</div>
						</div>

						{/* In Progress Callout */}
						{!session.is_completed && (
							<div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm flex items-start gap-3">
								<AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
								<div>
									<p className="font-bold">This interview is still in progress</p>
									<p className="text-xs text-amber-700 mt-1">
										A full evaluation report and progression trends will be generated once the interview is completed.
									</p>
									<Link to={`/interview/${session.id}`} className="inline-block mt-3">
										<Button size="sm" className="bg-amber-600 hover:bg-amber-700 text-white gap-1.5">
											Resume Interview
										</Button>
									</Link>
								</div>
							</div>
						)}

						{/* Interview Syllabus / Topic List */}
						{session.topic_list && session.topic_list.length > 0 && (
							<div className="p-6 bg-slate-50 border border-slate-200 rounded-xl flex flex-col gap-4">
								<div>
									<h3 className="text-md font-bold text-slate-900 flex items-center gap-2">
										<BookOpen className="h-4.5 w-4.5 text-indigo-600" />
										Planned Interview Syllabus
									</h3>
									<p className="text-xs text-slate-500 mt-1">
										These are the core subtopics selected for this mock interview session.
									</p>
								</div>
								<div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
									{session.topic_list.map((topic, index) => {
										const isCurrent = session.current_topic === topic;
										const isCompleted = !session.remaining_topics.includes(topic) && !isCurrent;
										
										return (
											<div
												key={index}
												className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 transition-all ${
													isCurrent
														? "bg-indigo-50 border-indigo-200 text-indigo-900 shadow-sm"
														: isCompleted
														? "bg-slate-100/50 border-slate-200 text-slate-500 opacity-75"
														: "bg-white border-slate-200 text-slate-700"
												}`}
											>
												<span className="text-xs font-semibold leading-tight">{topic}</span>
												{isCurrent ? (
													<span className="px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider bg-indigo-600 text-white animate-pulse">
														Active
													</span>
												) : isCompleted ? (
													<CheckCircle className="h-4 w-4 text-emerald-600 flex-shrink-0" />
												) : (
													<span className="h-1.5 w-1.5 rounded-full bg-slate-300 flex-shrink-0" />
												)}
											</div>
										);
									})}
								</div>
							</div>
						)}

						{/* Report Dashboard Section */}
						{session.is_completed && session.report && session.report.granular_averages && (
							<div className="grid gap-6 md:grid-cols-3">
								{/* Left: Summary and Strengths/Weaknesses */}
								<div className="md:col-span-2 flex flex-col gap-6">
									<div className="p-6 bg-slate-50 border border-slate-200 rounded-xl flex flex-col gap-3">
										<h3 className="text-md font-bold text-slate-900">Performance Summary</h3>
										<p className="text-sm text-slate-600 leading-relaxed">
											{session.report.summary}
										</p>
									</div>

									<div className="grid gap-4 sm:grid-cols-2">
										<div className="p-5 bg-emerald-50/60 border border-emerald-100/80 rounded-xl flex flex-col gap-3">
											<h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
												<CheckCircle className="h-4 w-4 text-emerald-600" />
												Key Strengths
											</h4>
											<ul className="text-xs text-emerald-950 flex flex-col gap-2 list-disc list-inside leading-relaxed">
												{session.report.strengths.map((str, index) => (
													<li key={index}>{str}</li>
												))}
											</ul>
										</div>

										<div className="p-5 bg-rose-50/60 border border-rose-100/80 rounded-xl flex flex-col gap-3">
											<h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
												<AlertTriangle className="h-4 w-4 text-rose-600" />
												Areas for Improvement
											</h4>
											<ul className="text-xs text-rose-950 flex flex-col gap-2 list-disc list-inside leading-relaxed">
												{session.report.weaknesses.map((weak, index) => (
													<li key={index}>{weak}</li>
												))}
											</ul>
										</div>
									</div>
								</div>

								{/* Right: Score Breakdown Metrics */}
								<div className="p-6 bg-slate-50 border border-slate-200 rounded-xl flex flex-col gap-4">
									<h3 className="text-md font-bold text-slate-900">Evaluation Metrics</h3>
									<div className="flex flex-col gap-4">
										{[
											{ label: "Technical Accuracy", value: session.report.granular_averages.accuracy },
											{ label: "Communication Skills", value: session.report.granular_averages.communication },
											{ label: "Confidence", value: session.report.granular_averages.confidence },
											{ label: "Answer Completeness", value: session.report.granular_averages.completeness },
										].map((metric) => (
											<div key={metric.label} className="flex flex-col gap-1.5">
												<div className="flex justify-between text-xs font-bold text-slate-700">
													<span>{metric.label}</span>
													<span>{Math.round(metric.value * 100)}%</span>
												</div>
												<div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
													<div
														className="bg-indigo-600 h-full rounded-full transition-all duration-500"
														style={{ width: `${metric.value * 100}%` }}
													/>
												</div>
											</div>
										))}
									</div>
								</div>
							</div>
						)}

						{/* Progression Trend Graph */}
						{session.is_completed && chartData.length > 0 && (
							<div className="p-6 bg-slate-50 border border-slate-200 rounded-xl flex flex-col gap-4">
								<div>
									<h3 className="text-md font-bold text-slate-900">Performance Progression</h3>
									<p className="text-xs text-slate-500 mt-1">
										Visualizes your score changes throughout the session (adaptive difficulty progression).
									</p>
								</div>
								<div className="h-64 w-full mt-2">
									<ResponsiveContainer width="100%" height="100%">
										<LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
											<defs>
												<linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
													<stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8} />
													<stop offset="95%" stopColor="#4f46e5" stopOpacity={0.1} />
												</linearGradient>
											</defs>
											<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
											<XAxis dataKey="name" stroke="#64748b" fontSize={11} fontWeight={600} />
											<YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} fontWeight={600} tickFormatter={(v) => `${v}%`} />
											<Tooltip
												formatter={(value: any) => [`${value}%`, "Score"]}
												contentStyle={{ backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}
											/>
											<Line
												type="monotone"
												dataKey="score"
												stroke="#4f46e5"
												strokeWidth={2.5}
												dot={{ r: 4, stroke: "#4f46e5", strokeWidth: 2, fill: "#fff" }}
												activeDot={{ r: 6 }}
											/>
										</LineChart>
									</ResponsiveContainer>
								</div>
							</div>
						)}

						{/* Conversation Transcript Review */}
						{session.history && session.history.length > 0 && (
							<div className="flex flex-col gap-4">
								<h3 className="text-lg font-bold text-slate-900">Transcript & Feedback Review</h3>
								<div className="flex flex-col gap-4">
									{session.history.map((entry, index) => (
										<div key={index} className="border border-slate-200 rounded-xl overflow-hidden">
											{/* Q&A Exchange Header */}
											<div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center flex-wrap gap-2">
												<span className="text-xs font-bold text-slate-700">
													Question #{index + 1}
												</span>
												{entry.score !== undefined && entry.score !== null && (
													<span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 border border-indigo-200 text-indigo-700">
														Score: {Math.round(entry.score * 100)}%
													</span>
												)}
											</div>

											{/* Dialogue exchanges */}
											<div className="p-4 flex flex-col gap-4">
												{/* Question from Kira */}
												<div className="flex gap-3">
													<div className="h-7 w-7 rounded-full bg-slate-900 flex-shrink-0 flex items-center justify-center text-white text-[10px] font-bold uppercase">
														K
													</div>
													<div className="bg-slate-100/80 rounded-xl p-3 text-xs text-slate-800 flex flex-col gap-1 w-full max-w-[85%] text-left">
														<span className="font-bold text-slate-900">Kira (Interviewer)</span>
														{renderQuestionTextAndCode(entry.question)}
													</div>
												</div>

												{/* Answer from Candidate */}
												{entry.answer ? (
													<div className="flex gap-3 justify-end">
														<div className="bg-indigo-50/80 rounded-xl p-3 text-xs text-indigo-900 flex flex-col gap-1 w-full max-w-[85%]">
															<span className="font-bold text-indigo-950">You (Candidate)</span>
															<p>{entry.answer}</p>
														</div>
														<div className="h-7 w-7 rounded-full bg-indigo-600 flex-shrink-0 flex items-center justify-center text-white">
															<User className="h-4 w-4" />
														</div>
													</div>
												) : (
													<div className="flex gap-3 justify-end">
														<div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-400 italic w-full max-w-[85%]">
															No response provided.
														</div>
													</div>
												)}

												{/* Specific Question Evaluation/Feedback */}
												{entry.feedback && (
													<div className="mt-2 border-t border-slate-100 pt-3 flex gap-2 text-xs">
														<HelpCircle className="h-4 w-4 text-indigo-500 mt-0.5 flex-shrink-0" />
														<div className="flex flex-col gap-1 text-slate-600">
															<span className="font-bold text-slate-800">Evaluator Feedback</span>
															<p>{entry.feedback}</p>
															{entry.granular_scores && (
																<div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[10px] text-slate-500 font-bold uppercase">
																	<span>Acc: {Math.round(entry.granular_scores.accuracy * 100)}%</span>
																	<span>Comm: {Math.round(entry.granular_scores.communication * 100)}%</span>
																	<span>Conf: {Math.round(entry.granular_scores.confidence * 100)}%</span>
																	<span>Comp: {Math.round(entry.granular_scores.completeness * 100)}%</span>
																</div>
															)}
														</div>
													</div>
												)}
											</div>
										</div>
									))}
								</div>
							</div>
						)}
					</div>
				)}
			</main>
		</div>
	);
}
