import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { ImageIcon, LayoutDashboard } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import BatchMonitor from "./pages/BatchMonitor";
import Gallery from "./pages/Gallery";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/gallery", label: "Galerie", icon: ImageIcon },
];

function Sidebar() {
  const location = useLocation();

  return (
    <aside className="flex flex-col w-56 shrink-0 border-r border-border bg-card min-h-screen">
      <div className="flex items-center gap-2 px-4 py-5 border-b border-border">
        <ImageIcon className="h-6 w-6 text-primary" />
        <span className="font-semibold text-sm">WSK Image Scraper</span>
      </div>

      <nav className="flex flex-col gap-1 p-2 mt-2">
        {navItems.map((item) => {
          const active =
            item.to === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.to);

          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/batches/:id" element={<BatchMonitor />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}
