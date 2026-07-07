import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { useInterviews } from "@/hooks/useInterview";
import { Calendar, Award, Clock, ArrowLeft, PlayCircle, BookOpen } from "lucide-react";

export default function History() {
	const { data: interviews, isLoading, error } = useInterviews();

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

	return (
		<div className="min-h-screen bg-white text-slate-900 flex flex-col font-sans">
			<Header />

			<main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
				<div className="flex items-center gap-3 mb-6">
					<Link to="/">
						<Button variant="ghost" size="sm" className="gap-1.5 text-slate-500 hover:text-slate-900">
							<ArrowLeft className="h-4 w-4" />
							Dashboard
						</Button>
					</Link>
				</div>

				<div className="border-b border-slate-200 pb-5 mb-8">
					<h1 className="text-3xl font-bold tracking-tight text-slate-900">
						Interview History
					</h1>
					<p className="text-slate-500 mt-2">
						Review your past sessions, check your evaluations, and trace your progress.
					</p>
				</div>

				{isLoading ? (
					<div className="flex flex-col items-center justify-center py-12 gap-3">
						<span className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
						<span className="text-sm text-slate-500">Loading history...</span>
					</div>
				) : error ? (
					<div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
						Failed to load interview history: {error.message}
					</div>
				) : !interviews || interviews.length === 0 ? (
					<div className="flex flex-col items-center justify-center py-16 border-2 border-dashed border-slate-200 rounded-2xl gap-4">
						<div className="h-12 w-12 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
							<BookOpen className="h-6 w-6" />
						</div>
						<div className="text-center">
							<p className="font-semibold text-slate-900">No mock sessions found</p>
							<p className="text-sm text-slate-500 mt-1">Start a mock interview from the dashboard first.</p>
						</div>
						<Link to="/">
							<Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
								Go to Dashboard
							</Button>
						</Link>
					</div>
				) : (
					<div className="grid gap-4">
						{interviews.map((session) => {
							const score = getScore(session.report);
							return (
								<div
									key={session.id}
									className="p-5 bg-slate-50 border border-slate-200 rounded-xl hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
								>
									<div className="flex flex-col gap-1.5">
										<div className="flex items-center gap-2 flex-wrap">
											<span className="text-sm font-bold text-slate-900 capitalize">
												{session.current_topic || "Topic Selection"}
											</span>
											<span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-200 text-slate-700 border border-slate-300/40">
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

										<div className="flex items-center gap-4 text-xs text-slate-500 mt-1 flex-wrap">
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

									<div className="flex items-center gap-4 justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-200/60">
										{score !== null ? (
											<div className="flex items-center gap-2">
												<Award className="h-5 w-5 text-indigo-600" />
												<div className="flex flex-col">
													<span className="text-[10px] text-slate-400 font-bold uppercase leading-none">
														Overall Score
													</span>
													<span className="text-lg font-bold text-slate-900 leading-tight">
														{score}%
													</span>
												</div>
											</div>
										) : (
											<span className="text-xs text-slate-400 font-medium">No report generated</span>
										)}

										<Link to={`/history/${session.id}`}>
											<Button
												size="sm"
												variant={session.is_completed ? "outline" : "default"}
												className={session.is_completed ? "border-slate-300 hover:bg-slate-100" : "bg-indigo-600 hover:bg-indigo-700 text-white"}
											>
												{session.is_completed ? (
													"View Details"
												) : (
													<>
														<PlayCircle className="h-4 w-4" />
														Resume
													</>
												)}
											</Button>
										</Link>
									</div>
								</div>
							);
						})}
					</div>
				)}
			</main>
		</div>
	);
}
