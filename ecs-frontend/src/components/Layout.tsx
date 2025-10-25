import { Link, useLocation } from "react-router-dom";
import { Home, Zap, Calendar, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: Home },
  { path: "/vens", label: "VENs", icon: Zap },
  { path: "/events", label: "Events", icon: Calendar },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  const NavLinks = ({ mobile = false }: { mobile?: boolean }) => (
    <>
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname.startsWith(item.path);
        return (
          <Link key={item.path} to={item.path}>
            <Button
              variant={isActive ? "default" : "ghost"}
              className={`w-full justify-start ${mobile ? "mb-2" : ""}`}
            >
              <Icon className="mr-2 h-4 w-4" />
              {item.label}
            </Button>
          </Link>
        );
      })}
    </>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <Link to="/dashboard" className="mr-6 flex items-center space-x-2">
              <Zap className="h-6 w-6" />
              <span className="font-bold">Grid Services</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-2 flex-1">
            <NavLinks />
          </nav>

          {/* Mobile Navigation */}
          <Sheet>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left">
              <nav className="flex flex-col mt-8">
                <NavLinks mobile />
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-6">{children}</main>
    </div>
  );
}
