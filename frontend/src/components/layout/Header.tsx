import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

export function Header() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout.mutateAsync();
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight text-slate-900">
            Kira
          </span>
        </Link>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-sm text-slate-600">
                Hi, <span className="font-medium text-slate-900">{user.name}</span>
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button size="sm">Sign In</Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
