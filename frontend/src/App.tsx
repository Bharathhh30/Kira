import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Interview from "./pages/Interview";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import History from "./pages/History";
import SessionDetails from "./pages/SessionDetails";
import Setup from "./pages/Setup";

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			refetchOnWindowFocus: false,
			retry: false,
		},
	},
});

export default function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<BrowserRouter>
				<Routes>
					<Route path="/" element={<Landing />} />
					<Route path="/login" element={<Login />} />
					<Route path="/register" element={<Register />} />
					<Route path="/profile" element={<Profile />} />
					<Route path="/interview/:id" element={<Interview />} />
					<Route path="/history" element={<History />} />
					<Route path="/history/:id" element={<SessionDetails />} />
					<Route path="/setup" element={<Setup />} />
				</Routes>
			</BrowserRouter>
		</QueryClientProvider>
	);
}
