import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface GranularScores {
	communication: number;
	accuracy: number;
	confidence: number;
	completeness: number;
}

export interface InterviewHistoryEntry {
	question: string;
	answer?: string;
	score?: number;
	feedback?: string;
	timestamp: string;
	granular_scores?: GranularScores;
}

export interface EvaluationReport {
	summary: string;
	strengths: string[];
	weaknesses: string[];
	granular_averages: {
		communication: number;
		accuracy: number;
		confidence: number;
		completeness: number;
	};
}

export interface InterviewResponseData {
	id: string;
	user_id: string;
	current_topic: string | null;
	remaining_topics: string[];
	current_question: string | null;
	follow_up_count: number;
	history: InterviewHistoryEntry[];
	remaining_time: number;
	interview_mode: string;
	is_completed: boolean;
	report?: EvaluationReport;
	created_at: string;
}

export function useInterview(
	interviewId?: string,
	refetchInterval: number | false = false,
) {
	const queryClient = useQueryClient();

	const interviewQuery = useQuery<InterviewResponseData>({
		queryKey: ["interview", interviewId],
		queryFn: async () => {
			if (!interviewId) throw new Error("No interview ID provided");
			const response = await api.get(`/interview/state/${interviewId}`);
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || "Failed to fetch interview state");
			}
			return response.json();
		},
		enabled: !!interviewId,
		refetchInterval,
	});

	const startMutation = useMutation<
		InterviewResponseData,
		Error,
		{ mode?: string; job_description?: string; company_name?: string }
	>({
		mutationFn: async ({ mode = "resume", job_description, company_name } = {}) => {
			const response = await api.post("/interview/start", {
				interview_mode: mode,
				job_description,
				company_name,
			});
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || "Failed to start interview");
			}
			return response.json();
		},
	});

	const nextMutation = useMutation<
		InterviewResponseData,
		Error,
		{ answer: string }
	>({
		mutationFn: async ({ answer }) => {
			if (!interviewId) throw new Error("No active interview session");
			const response = await api.post(`/interview/next/${interviewId}`, {
				answer,
			});
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || "Failed to submit answer");
			}
			return response.json();
		},
		onSuccess: (data) => {
			queryClient.setQueryData(["interview", interviewId], data);
		},
	});

	const endMutation = useMutation<
		InterviewResponseData,
		Error,
		void
	>({
		mutationFn: async () => {
			if (!interviewId) throw new Error("No active interview session");
			const response = await api.post(`/interview/end/${interviewId}`);
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || "Failed to end interview early");
			}
			return response.json();
		},
		onSuccess: (data) => {
			queryClient.setQueryData(["interview", interviewId], data);
		},
	});

	return {
		interview: interviewQuery.data,
		isLoading: interviewQuery.isLoading,
		error: interviewQuery.error,
		refetchState: interviewQuery.refetch,
		startInterview: startMutation,
		submitAnswer: nextMutation,
		endInterviewEarly: endMutation,
	};
}

export function useInterviewToken(interviewId?: string) {
	return useQuery<{ token: string; server_url: string }>({
		queryKey: ["interview-token", interviewId],
		queryFn: async () => {
			if (!interviewId) throw new Error("No interview ID provided");
			const response = await api.post(`/interview/token/${interviewId}`);
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || "Failed to fetch LiveKit token");
			}
			return response.json();
		},
		enabled: !!interviewId,
		staleTime: 5 * 60 * 1000,
	});
}
