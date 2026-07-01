import { LoginForm } from "@/components/login-form";

export default function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6 sm:p-10">
      <div className="w-full max-w-sm">
        <LoginForm />
      </div>
    </div>
  );
}
