import { SignupForm } from "@/components/signup-form";

export default function Register() {
	return (
		<div className="flex min-h-screen items-center justify-center bg-slate-50 p-6 sm:p-10">
			<div className="w-full max-w-md">
				<SignupForm />
			</div>
		</div>
	);
}
