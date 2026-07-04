import {
	LiveKitRoom,
	RoomAudioRenderer,
	useLocalParticipant,
} from "@livekit/components-react";
import {
	AlertCircle,
	ArrowLeft,
	Award,
	CheckCircle,
	HelpCircle,
	MessageSquare,
	Mic,
	MicOff,
	Send,
	Timer,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useInterview, useInterviewToken } from "@/hooks/useInterview";

interface VoiceControlsProps {
	onDisconnect: () => void;
}

function VoiceControls({ onDisconnect }: VoiceControlsProps) {
	const { localParticipant } = useLocalParticipant();
	const [isMuted, setIsMuted] = useState(false);

	useEffect(() => {
		if (localParticipant) {
			localParticipant.setMicrophoneEnabled(!isMuted);
		}
	}, [isMuted, localParticipant]);

	return (
		<div className="p-4 bg-white border-t border-slate-200 flex items-center justify-between gap-4">
			<div className="flex items-center gap-2">
				<span className="relative flex h-2 w-2">
					<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
					<span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
				</span>
				<span className="text-xs font-semibold text-slate-600">
					{isMuted ? "Voice Muted" : "Voice Connected (Kira is listening)"}
				</span>
			</div>

			{/* Pulsing visualizer bars */}
			{!isMuted && (
				<div className="flex items-center gap-1.5 px-4 h-6">
					<span
						className="h-3.5 w-1 bg-emerald-500 rounded-full animate-bounce"
						style={{ animationDelay: "0ms" }}
					/>
					<span
						className="h-5 w-1 bg-emerald-500 rounded-full animate-bounce"
						style={{ animationDelay: "150ms" }}
					/>
					<span
						className="h-4 w-1 bg-emerald-500 rounded-full animate-bounce"
						style={{ animationDelay: "300ms" }}
					/>
					<span
						className="h-6 w-1 bg-emerald-500 rounded-full animate-bounce"
						style={{ animationDelay: "450ms" }}
					/>
					<span
						className="h-3 w-1 bg-emerald-500 rounded-full animate-bounce"
						style={{ animationDelay: "600ms" }}
					/>
				</div>
			)}

			<div className="flex items-center gap-2">
				<Button
					type="button"
					variant="outline"
					size="sm"
					className="border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900 rounded-lg cursor-pointer flex items-center gap-1 text-xs font-semibold"
					onClick={() => setIsMuted(!isMuted)}
				>
					{isMuted ? (
						<Mic className="h-3.5 w-3.5 text-red-500" />
					) : (
						<MicOff className="h-3.5 w-3.5 text-slate-500" />
					)}
					<span>{isMuted ? "Unmute" : "Mute"}</span>
				</Button>
				<Button
					type="button"
					variant="outline"
					size="sm"
					className="border-red-250 text-red-650 hover:bg-red-50/50 rounded-lg cursor-pointer text-xs font-semibold"
					onClick={onDisconnect}
				>
					End Voice
				</Button>
			</div>
		</div>
	);
}

export default function Interview() {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();

	const [isVoiceMode, setIsVoiceMode] = useState(false);
	const [answer, setAnswer] = useState("");
	const [charCount, setCharCount] = useState(0);

	// Poll every 2 seconds when in Voice Mode to display transcripts in real-time
	const refetchInterval = isVoiceMode ? 2000 : false;
	const { interview, isLoading, error, submitAnswer } = useInterview(
		id,
		refetchInterval,
	);

	const {
		data: tokenData,
		isLoading: isLoadingToken,
		error: tokenError,
	} = useInterviewToken(isVoiceMode ? id : undefined);

	const chatEndRef = useRef<HTMLDivElement>(null);

	// Scroll to bottom on new messages
	useEffect(() => {
		chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [interview?.history, interview?.current_question]);

	useEffect(() => {
		setCharCount(answer.length);
	}, [answer]);

	if (isLoading) {
		return (
			<div className="min-h-screen bg-white text-slate-900 flex flex-col justify-center items-center gap-4">
				<span className="h-10 w-10 animate-spin rounded-full border-4 border-slate-300 border-t-slate-900" />
				<p className="text-slate-500 font-medium">
					Connecting to interview session...
				</p>
			</div>
		);
	}

	if (error || !interview) {
		return (
			<div className="min-h-screen bg-white text-slate-900 flex flex-col justify-center items-center p-6 gap-6">
				<div className="bg-red-50 border border-red-200 p-6 rounded-xl text-center max-w-md">
					<AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
					<h3 className="text-xl font-bold text-slate-900 mb-2">
						Failed to load session
					</h3>
					<p className="text-slate-600 text-sm mb-4">
						{error
							? error.message
							: "The requested interview session could not be found."}
					</p>
					<Link to="/">
						<Button className="bg-slate-900 hover:bg-slate-800 text-white">
							Back to Dashboard
						</Button>
					</Link>
				</div>
			</div>
		);
	}

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!answer.trim() || submitAnswer.isPending) return;

		try {
			await submitAnswer.mutateAsync({ answer });
			setAnswer("");
		} catch (err) {
			console.error("Failed to submit answer:", err);
		}
	};

	// Calculate average score
	const scoredHistory = interview.history.filter((h) => h.score !== null);
	const averageScore =
		scoredHistory.length > 0
			? (scoredHistory.reduce((sum, h) => sum + (h.score || 0), 0) /
					scoredHistory.length) *
				100
			: 0;

	// Format remaining time
	const formatTime = (secs: number) => {
		const mins = Math.floor(secs / 60);
		const remainingSecs = secs % 60;
		return `${mins}:${remainingSecs.toString().padStart(2, "0")}`;
	};

	return (
		<div className="min-h-screen bg-white text-slate-900 flex flex-col font-sans">
			<Header />

			{/* Custom Top Dashboard Bar */}
			<div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
				<div className="flex items-center gap-3">
					<Button
						variant="ghost"
						size="icon"
						className="text-slate-500 hover:text-slate-950 cursor-pointer"
						onClick={() => navigate("/")}
					>
						<ArrowLeft className="h-5 w-5" />
					</Button>
					<div>
						<h2 className="font-bold text-lg text-slate-900 flex items-center gap-2">
							<span>Technical Mock Interview</span>
							<span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 capitalize">
								{interview.interview_mode} Mode
							</span>
						</h2>
					</div>
				</div>

				<div className="flex items-center gap-6">
					<div className="flex items-center gap-2 text-slate-600">
						<Timer className="h-5 w-5 text-slate-500" />
						<span className="font-mono font-bold text-lg text-slate-900">
							{formatTime(interview.remaining_time)}
						</span>
					</div>
				</div>
			</div>

			<div className="flex-1 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-4 gap-6 p-6 overflow-hidden">
				{/* Sidebar details */}
				<div className="lg:col-span-1 flex flex-col gap-5">
					{/* Active status */}
					<Card className="bg-slate-50 border-slate-200 p-5 flex flex-col gap-4 shadow-sm">
						<div>
							<span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
								Current Topic
							</span>
							<h3 className="text-xl font-extrabold text-slate-900 mt-1">
								{interview.current_topic || "Completed"}
							</h3>
						</div>

						{interview.follow_up_count > 0 && (
							<div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
								<AlertCircle className="h-4 w-4 text-amber-600" />
								<span className="text-xs text-amber-700 font-medium">
									Follow-up Probing #{interview.follow_up_count}
								</span>
							</div>
						)}
					</Card>

					{/* Topics Queue */}
					<Card className="bg-slate-50 border-slate-200 p-5 flex flex-col gap-3 flex-1 shadow-sm">
						<h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 pb-2">
							Interview Syllabus
						</h4>
						<div className="flex flex-col gap-2 overflow-y-auto max-h-[300px] lg:max-h-none pr-1">
							{/* Current active topic */}
							{interview.current_topic && (
								<div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-900 text-white font-semibold text-sm">
									<span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
									<span className="truncate">{interview.current_topic}</span>
								</div>
							)}

							{/* Upcoming topics */}
							{interview.remaining_topics.map((topic, idx) => (
								<div
									key={idx}
									className="flex items-center gap-2 p-2.5 rounded-lg bg-white border border-slate-200/60 text-slate-500 text-sm"
								>
									<span className="h-1.5 w-1.5 rounded-full bg-slate-300" />
									<span className="truncate">{topic}</span>
								</div>
							))}
						</div>
					</Card>
				</div>

				{/* Chat Area / Main view */}
				<div className="lg:col-span-3 flex flex-col bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden h-[600px] lg:h-[700px] shadow-sm animate-fade-in">
					{/* Toggle Header */}
					{!interview.is_completed && (
						<div className="bg-white border-b border-slate-200 px-4 py-2.5 flex items-center justify-between">
							<span className="text-xs font-bold text-slate-500 flex items-center gap-1.5 uppercase tracking-wider">
								<span className="h-2 w-2 rounded-full bg-emerald-500" />
								Session Active
							</span>
							<Button
								variant="outline"
								size="sm"
								className="h-8.5 rounded-lg border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900 flex items-center gap-1.5 cursor-pointer text-xs font-semibold"
								onClick={() => setIsVoiceMode(!isVoiceMode)}
							>
								{isVoiceMode ? (
									<>
										<MessageSquare className="h-3.5 w-3.5" />
										<span>Switch to Text</span>
									</>
								) : (
									<>
										<Mic className="h-3.5 w-3.5 animate-pulse" />
										<span>Switch to Voice</span>
									</>
								)}
							</Button>
						</div>
					)}

					{interview.is_completed ? (
						/* Complete Screen */
						<div className="flex-1 overflow-y-auto p-8 flex flex-col justify-center items-center text-center gap-6">
							<div className="h-20 w-20 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 animate-bounce">
								<Award className="h-10 w-10" />
							</div>

							<div className="flex flex-col gap-2">
								<h2 className="text-3xl font-extrabold text-slate-900">
									Interview Complete!
								</h2>
								<p className="text-slate-500 text-sm max-w-md">
									Congratulations on finishing this adaptive interview session.
									We have evaluated your answers.
								</p>
							</div>

							<div className="bg-white border border-slate-200 rounded-2xl p-6 w-full max-w-md flex flex-col gap-4 shadow-sm">
								<div className="flex justify-between items-center border-b border-slate-100 pb-3">
									<span className="text-slate-500 text-sm">
										Overall Performance Score
									</span>
									<span className="font-mono text-2xl font-black text-slate-900">
										{averageScore.toFixed(0)}%
									</span>
								</div>
								<div className="flex justify-between items-center text-sm">
									<span className="text-slate-500">Questions Answered</span>
									<span className="font-semibold text-slate-800">
										{interview.history.length}
									</span>
								</div>
							</div>

							<div className="flex gap-4">
								<Link to="/">
									<Button className="bg-slate-900 hover:bg-slate-800 text-white px-8 cursor-pointer">
										Return to Dashboard
									</Button>
								</Link>
							</div>
						</div>
					) : (
						/* Active Chat view */
						<>
							{/* Scrollable messages container */}
							<div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 scrollbar-thin scrollbar-thumb-slate-200">
								{/* Greeting message */}
								<div className="flex gap-3 max-w-[85%] self-start animate-fade-in">
									<div className="h-9 w-9 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 flex-shrink-0">
										<MessageSquare className="h-4.5 w-4.5" />
									</div>
									<div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-slate-800 text-sm leading-relaxed shadow-sm">
										<p>
											Welcome to your session! I'll guide you through questions
											about your resume, starting with your technical
											experience.
										</p>
									</div>
								</div>

								{/* Timeline of exchanges */}
								{interview.history.map((turn, index) => (
									<div key={index} className="flex flex-col gap-5">
										{/* AI Question */}
										<div className="flex gap-3 max-w-[85%] self-start">
											<div className="h-9 w-9 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 flex-shrink-0">
												<HelpCircle className="h-4.5 w-4.5" />
											</div>
											<div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-slate-800 text-sm leading-relaxed shadow-sm">
												<p>{turn.question}</p>
											</div>
										</div>

										{/* Candidate Answer */}
										{turn.answer && (
											<div className="flex gap-3 max-w-[85%] self-end">
												<div className="bg-slate-900 text-white rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm">
													<p>{turn.answer}</p>
												</div>
											</div>
										)}

										{/* Feedback/Score block */}
										{turn.feedback && (
											<div className="ml-12 p-3.5 bg-white border border-slate-200/80 rounded-xl flex gap-3 max-w-[75%] self-start shadow-sm">
												<div className="h-7 w-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-800 text-xs font-bold font-mono">
													{Math.round((turn.score || 0) * 10)}
												</div>
												<div className="text-slate-600 text-xs leading-relaxed">
													<span className="font-bold text-slate-800">
														Feedback:
													</span>{" "}
													{turn.feedback}
												</div>
											</div>
										)}
									</div>
								))}

								{/* Current AI Question */}
								{interview.current_question && (
									<div className="flex gap-3 max-w-[85%] self-start animate-fade-in">
										<div className="h-9 w-9 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 flex-shrink-0 animate-pulse">
											<HelpCircle className="h-4.5 w-4.5" />
										</div>
										<div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-slate-800 text-sm leading-relaxed shadow-sm">
											<p>{interview.current_question}</p>
										</div>
									</div>
								)}

								<div ref={chatEndRef} />
							</div>

							{/* Chat input box / LiveKit audio panel */}
							{isVoiceMode ? (
								isLoadingToken ? (
									<div className="p-4 bg-white border-t border-slate-200 flex items-center justify-center gap-2 text-slate-500 text-sm font-medium">
										<span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800" />
										<span>Generating voice room credentials...</span>
									</div>
								) : tokenError ? (
									<div className="p-4 bg-white border-t border-slate-200 text-red-600 text-sm font-medium text-center">
										Failed to connect to voice service. Please switch back to
										text mode.
									</div>
								) : tokenData ? (
									<LiveKitRoom
										serverUrl={tokenData.server_url}
										token={tokenData.token}
										connect={true}
										audio={true}
										video={false}
										onDisconnected={() => setIsVoiceMode(false)}
									>
										<RoomAudioRenderer />
										<VoiceControls onDisconnect={() => setIsVoiceMode(false)} />
									</LiveKitRoom>
								) : null
							) : (
								<form
									onSubmit={handleSubmit}
									className="p-4 bg-white border-t border-slate-200 flex flex-col gap-2"
								>
									<div className="flex items-center gap-3">
										<input
											type="text"
											className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-slate-300 placeholder-slate-400 transition-colors"
											placeholder="Type your response here..."
											value={answer}
											onChange={(e) => setAnswer(e.target.value)}
											disabled={submitAnswer.isPending}
										/>
										<Button
											type="submit"
											className="bg-slate-900 hover:bg-slate-800 text-white rounded-xl h-11 w-11 flex items-center justify-center flex-shrink-0 transition-colors cursor-pointer"
											disabled={submitAnswer.isPending || !answer.trim()}
										>
											{submitAnswer.isPending ? (
												<span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
											) : (
												<Send className="h-4 w-4" />
											)}
										</Button>
									</div>

									{/* Guidance indicators */}
									<div className="flex items-center justify-between px-1.5 text-xs">
										<div className="flex items-center gap-1.5">
											{charCount < 20 ? (
												<>
													<AlertCircle className="h-3.5 w-3.5 text-amber-600" />
													<span className="text-amber-700/90 font-medium">
														Under 20 characters (will trigger a probing
														follow-up)
													</span>
												</>
											) : (
												<>
													<CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
													<span className="text-emerald-700/90 font-medium">
														Sufficient answer length to transition topics
													</span>
												</>
											)}
										</div>
										<span
											className={`font-mono font-medium ${
												charCount < 20 ? "text-amber-600" : "text-emerald-600"
											}`}
										>
											{charCount} chars
										</span>
									</div>
								</form>
							)}
						</>
					)}
				</div>
			</div>
		</div>
	);
}
