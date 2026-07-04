import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

interface ResumeResponseData {
	id: string;
	user_id: string;
	resume_json: {
		personal?: {
			name?: string;
			email?: string;
			phone?: string;
			location?: string;
			summary?: string;
		};
		links?: {
			linkedin?: string;
			github?: string;
			portfolio?: string;
			leetcode?: string;
			codeforces?: string;
			other?: string[];
		};
		skills?: {
			technical?: string[];
			languages_spoken?: string[];
			tools?: string[];
		};
		experience?: {
			company: string;
			title?: string;
			start_date?: string;
			end_date?: string;
			location?: string;
			bullets?: string[];
			technologies?: string[];
			github_url?: string;
		}[];
		education?: {
			institution: string;
			degree?: string;
			field?: string;
			start_date?: string;
			end_date?: string;
			gpa?: number;
			honors?: string[];
		}[];
		projects?: {
			name: string;
			description?: string;
			technologies?: string[];
			github_url?: string;
			live_url?: string;
			dates?: string;
		}[];
		certifications?: {
			name: string;
			issuer?: string;
			date?: string;
			url?: string;
		}[];
		achievements?: string[];
		coding_profiles?: {
			leetcode_rating?: string;
			codechef_rating?: string;
			codeforces_rating?: string;
		};
	};
	parsed_at: string;
}

export default function Profile() {
	const { user } = useAuth();

	const {
		data: resume,
		isLoading,
		error,
	} = useQuery<ResumeResponseData | null>({
		queryKey: ["resume"],
		queryFn: async () => {
			const res = await api.get("/auth/resume");
			if (res.status === 404) {
				return null;
			}
			if (!res.ok) {
				throw new Error("Failed to fetch resume");
			}
			return res.json();
		},
	});

	return (
		<div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
			<Header />

			<main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12">
				{isLoading ? (
					<div className="flex flex-col items-center justify-center py-20 gap-4">
						<span className="h-8 w-8 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
						<span className="text-slate-500 font-medium">
							Loading profile details...
						</span>
					</div>
				) : error ? (
					<div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-center max-w-md mx-auto">
						<h3 className="font-semibold mb-2">Error Loading Profile</h3>
						<p className="text-sm">
							{(error as Error).message || "An unexpected error occurred."}
						</p>
					</div>
				) : !resume ? (
					/* Empty State: Prompt user to upload resume */
					<div className="bg-white border border-slate-200 rounded-xl p-12 text-center max-w-lg mx-auto shadow-sm flex flex-col items-center gap-6 mt-12">
						<div className="h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								strokeWidth={1.5}
								stroke="currentColor"
								className="w-8 h-8"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12-3-3m0 0-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
								/>
							</svg>
						</div>
						<div className="flex flex-col gap-2">
							<h2 className="text-xl font-bold text-slate-900">
								No Profile Data Available
							</h2>
							<p className="text-slate-500 text-sm max-w-sm">
								We couldn't find any parsed resume details. Upload your PDF
								resume on the home page, and we'll automatically construct this
								profile for you.
							</p>
						</div>
						<Link to="/">
							<Button className="bg-slate-900 text-white hover:bg-slate-800 px-6">
								Go to Upload Resume
							</Button>
						</Link>
					</div>
				) : (
					/* Profile Content View */
					<div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start animate-fade-in">
						{/* Left Sidebar Column */}
						<div className="flex flex-col gap-6 lg:col-span-1">
							{/* Personal details card */}
							<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
								<div>
									<h2 className="text-2xl font-bold text-slate-900">
										{resume.resume_json.personal?.name || user?.name}
									</h2>
									<p className="text-slate-500 text-sm mt-1">
										{resume.resume_json.personal?.location}
									</p>
								</div>

								<div className="border-t border-slate-100 pt-4 flex flex-col gap-2 text-sm text-slate-700">
									{resume.resume_json.personal?.email && (
										<div className="flex items-center gap-2">
											<span className="text-slate-400 font-medium w-12">
												Email:
											</span>
											<a
												href={`mailto:${resume.resume_json.personal.email}`}
												className="hover:underline text-slate-900 font-medium truncate"
											>
												{resume.resume_json.personal.email}
											</a>
										</div>
									)}
									{resume.resume_json.personal?.phone && (
										<div className="flex items-center gap-2">
											<span className="text-slate-400 font-medium w-12">
												Phone:
											</span>
											<span className="text-slate-900 font-medium">
												{resume.resume_json.personal.phone}
											</span>
										</div>
									)}
								</div>

								{/* Social/Coding Profile Links */}
								{resume.resume_json.links && (
									<div className="border-t border-slate-100 pt-4 flex flex-col gap-2 text-sm">
										<span className="font-semibold text-slate-900">Links</span>
										<div className="flex flex-wrap gap-2 mt-1">
											{resume.resume_json.links.github && (
												<a
													href={resume.resume_json.links.github}
													target="_blank"
													rel="noreferrer"
													className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs rounded-full font-medium transition-colors"
												>
													GitHub
												</a>
											)}
											{resume.resume_json.links.linkedin && (
												<a
													href={resume.resume_json.links.linkedin}
													target="_blank"
													rel="noreferrer"
													className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs rounded-full font-medium transition-colors"
												>
													LinkedIn
												</a>
											)}
											{resume.resume_json.links.portfolio && (
												<a
													href={resume.resume_json.links.portfolio}
													target="_blank"
													rel="noreferrer"
													className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs rounded-full font-medium transition-colors"
												>
													Portfolio
												</a>
											)}
											{resume.resume_json.links.leetcode && (
												<a
													href={resume.resume_json.links.leetcode}
													target="_blank"
													rel="noreferrer"
													className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs rounded-full font-medium transition-colors"
												>
													LeetCode
												</a>
											)}
											{resume.resume_json.links.codeforces && (
												<a
													href={resume.resume_json.links.codeforces}
													target="_blank"
													rel="noreferrer"
													className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs rounded-full font-medium transition-colors"
												>
													Codeforces
												</a>
											)}
										</div>
									</div>
								)}
							</div>

							{/* Coding Ratings block */}
							{resume.resume_json.coding_profiles && (
								<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
									<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
										Coding Profiles & Ratings
									</h3>
									<div className="grid grid-cols-3 gap-4 text-center">
										{resume.resume_json.coding_profiles.leetcode_rating && (
											<div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
												<p className="text-[10px] text-slate-400 font-bold uppercase">
													LeetCode
												</p>
												<p className="text-lg font-extrabold text-slate-900 mt-1">
													{resume.resume_json.coding_profiles.leetcode_rating}
												</p>
											</div>
										)}
										{resume.resume_json.coding_profiles.codeforces_rating && (
											<div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
												<p className="text-[10px] text-slate-400 font-bold uppercase">
													Forces
												</p>
												<p className="text-lg font-extrabold text-slate-900 mt-1">
													{resume.resume_json.coding_profiles.codeforces_rating}
												</p>
											</div>
										)}
										{resume.resume_json.coding_profiles.codechef_rating && (
											<div className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
												<p className="text-[10px] text-slate-400 font-bold uppercase">
													CodeChef
												</p>
												<p className="text-lg font-extrabold text-slate-900 mt-1">
													{resume.resume_json.coding_profiles.codechef_rating}
												</p>
											</div>
										)}
									</div>
								</div>
							)}

							{/* Skills card */}
							{resume.resume_json.skills && (
								<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-5">
									<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
										Skills
									</h3>
									{resume.resume_json.skills.technical &&
										resume.resume_json.skills.technical.length > 0 && (
											<div className="flex flex-col gap-2">
												<span className="text-xs font-semibold text-slate-400 uppercase">
													Technical Skills
												</span>
												<div className="flex flex-wrap gap-1.5">
													{resume.resume_json.skills.technical.map(
														(sk, idx) => (
															<span
																key={idx}
																className="px-2.5 py-0.5 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded font-medium"
															>
																{sk}
															</span>
														),
													)}
												</div>
											</div>
										)}
									{resume.resume_json.skills.tools &&
										resume.resume_json.skills.tools.length > 0 && (
											<div className="flex flex-col gap-2 pt-2 border-t border-slate-100">
												<span className="text-xs font-semibold text-slate-400 uppercase">
													Tools & Frameworks
												</span>
												<div className="flex flex-wrap gap-1.5">
													{resume.resume_json.skills.tools.map((t, idx) => (
														<span
															key={idx}
															className="px-2.5 py-0.5 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded font-medium"
														>
															{t}
														</span>
													))}
												</div>
											</div>
										)}
									{resume.resume_json.skills.languages_spoken &&
										resume.resume_json.skills.languages_spoken.length > 0 && (
											<div className="flex flex-col gap-2 pt-2 border-t border-slate-100">
												<span className="text-xs font-semibold text-slate-400 uppercase">
													Languages
												</span>
												<div className="flex flex-wrap gap-1.5">
													{resume.resume_json.skills.languages_spoken.map(
														(l, idx) => (
															<span
																key={idx}
																className="px-2.5 py-0.5 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded font-medium"
															>
																{l}
															</span>
														),
													)}
												</div>
											</div>
										)}
								</div>
							)}
						</div>

						{/* Right Main details Column */}
						<div className="flex flex-col gap-6 lg:col-span-2">
							{/* Summary */}
							{resume.resume_json.personal?.summary && (
								<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
									<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2 mb-4">
										Professional Summary
									</h3>
									<p className="text-slate-600 text-sm leading-relaxed whitespace-pre-line">
										{resume.resume_json.personal.summary}
									</p>
								</div>
							)}

							{/* Experience timeline */}
							{resume.resume_json.experience &&
								resume.resume_json.experience.length > 0 && (
									<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-6">
										<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
											Professional Experience
										</h3>
										<div className="flex flex-col gap-8">
											{resume.resume_json.experience.map((exp, idx) => (
												<div
													key={idx}
													className="flex flex-col gap-2 group relative"
												>
													<div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
														<h4 className="font-bold text-slate-900 text-base">
															{exp.title}{" "}
															<span className="font-normal text-slate-400">
																at
															</span>{" "}
															{exp.company}
														</h4>
														<span className="text-xs text-slate-500 font-medium sm:text-right">
															{exp.start_date} – {exp.end_date || "Current"}
														</span>
													</div>
													{exp.location && (
														<p className="text-xs text-slate-400 font-medium -mt-1">
															{exp.location}
														</p>
													)}
													{exp.bullets && exp.bullets.length > 0 && (
														<ul className="list-disc pl-4 text-sm text-slate-600 flex flex-col gap-1.5 mt-2">
															{exp.bullets.map((b, bIdx) => (
																<li key={bIdx} className="leading-relaxed">
																	{b}
																</li>
															))}
														</ul>
													)}
													{exp.technologies && exp.technologies.length > 0 && (
														<div className="flex flex-wrap gap-1.5 mt-2">
															{exp.technologies.map((t, tIdx) => (
																<span
																	key={tIdx}
																	className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[10px] rounded font-medium"
																>
																	{t}
																</span>
															))}
														</div>
													)}
												</div>
											))}
										</div>
									</div>
								)}

							{/* Projects */}
							{resume.resume_json.projects &&
								resume.resume_json.projects.length > 0 && (
									<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-6">
										<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
											Key Projects
										</h3>
										<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
											{resume.resume_json.projects.map((proj, idx) => (
												<div
													key={idx}
													className="p-4 border border-slate-100 bg-slate-50/50 rounded-lg flex flex-col justify-between gap-3"
												>
													<div className="flex flex-col gap-1">
														<div className="flex justify-between items-start">
															<h4 className="font-bold text-slate-900 text-sm">
																{proj.name}
															</h4>
															{proj.dates && (
																<span className="text-[10px] text-slate-400 font-medium">
																	{proj.dates}
																</span>
															)}
														</div>
														{proj.description && (
															<p className="text-slate-600 text-xs leading-relaxed mt-1">
																{proj.description}
															</p>
														)}
													</div>
													<div className="flex flex-col gap-2">
														{proj.technologies &&
															proj.technologies.length > 0 && (
																<div className="flex flex-wrap gap-1 mt-1">
																	{proj.technologies.map((t, tIdx) => (
																		<span
																			key={tIdx}
																			className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[9px] rounded font-medium"
																		>
																			{t}
																		</span>
																	))}
																</div>
															)}
														<div className="flex gap-3 text-[10px] font-bold text-slate-700 mt-2">
															{proj.github_url && (
																<a
																	href={proj.github_url}
																	target="_blank"
																	rel="noreferrer"
																	className="hover:underline flex items-center gap-1"
																>
																	GitHub
																</a>
															)}
															{proj.live_url && (
																<a
																	href={proj.live_url}
																	target="_blank"
																	rel="noreferrer"
																	className="hover:underline flex items-center gap-1"
																>
																	Live Demo
																</a>
															)}
														</div>
													</div>
												</div>
											))}
										</div>
									</div>
								)}

							{/* Education list */}
							{resume.resume_json.education &&
								resume.resume_json.education.length > 0 && (
									<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
										<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
											Education
										</h3>
										<div className="flex flex-col gap-4">
											{resume.resume_json.education.map((edu, idx) => (
												<div
													key={idx}
													className="flex justify-between items-start gap-4"
												>
													<div className="flex flex-col gap-1">
														<h4 className="font-bold text-slate-900 text-sm">
															{edu.institution}
														</h4>
														<p className="text-xs text-slate-600 font-medium">
															{edu.degree}
															{edu.field ? ` in ${edu.field}` : ""}
														</p>
														{edu.gpa && (
															<p className="text-xs text-slate-400 mt-0.5">
																GPA:{" "}
																<span className="font-semibold text-slate-700">
																	{edu.gpa}
																</span>
															</p>
														)}
													</div>
													<span className="text-xs text-slate-500 font-medium whitespace-nowrap">
														{edu.start_date} – {edu.end_date || "Present"}
													</span>
												</div>
											))}
										</div>
									</div>
								)}

							{/* Certifications and Achievements split grid */}
							<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
								{/* Certifications */}
								{resume.resume_json.certifications &&
									resume.resume_json.certifications.length > 0 && (
										<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
											<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
												Certifications
											</h3>
											<ul className="flex flex-col gap-3">
												{resume.resume_json.certifications.map((c, idx) => (
													<li
														key={idx}
														className="text-xs text-slate-700 leading-relaxed"
													>
														<p className="font-bold text-slate-900">{c.name}</p>
														<p className="text-slate-400 mt-0.5">
															{c.issuer}
															{c.date ? ` • ${c.date}` : ""}
														</p>
													</li>
												))}
											</ul>
										</div>
									)}

								{/* Achievements */}
								{resume.resume_json.achievements &&
									resume.resume_json.achievements.length > 0 && (
										<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
											<h3 className="font-bold text-slate-900 text-sm tracking-wider uppercase border-b border-slate-100 pb-2">
												Achievements
											</h3>
											<ul className="list-disc pl-4 text-xs text-slate-600 flex flex-col gap-2">
												{resume.resume_json.achievements.map((ach, idx) => (
													<li key={idx} className="leading-relaxed">
														{ach}
													</li>
												))}
											</ul>
										</div>
									)}
							</div>
						</div>
					</div>
				)}
			</main>
		</div>
	);
}
