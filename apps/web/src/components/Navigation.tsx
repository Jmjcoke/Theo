import { Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  BookOpen, 
  MessageSquare, 
  Settings, 
  LogOut, 
  Home,
  Users,
  FileText,
  User
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const Navigation = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActivePath = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 py-4">
        <nav className="flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-primary">Theo</span>
          </Link>

          {/* Main Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <Link 
              to="/" 
              className={`flex items-center space-x-2 text-sm font-medium transition-colors hover:text-primary ${
                isActivePath('/') && location.pathname === '/' ? 'text-primary' : 'text-muted-foreground'
              }`}
            >
              <Home className="w-4 h-4" />
              <span>Home</span>
            </Link>
            
            <Link 
              to="/chat" 
              className={`flex items-center space-x-2 text-sm font-medium transition-colors hover:text-primary ${
                isActivePath('/chat') ? 'text-primary' : 'text-muted-foreground'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Research Chat</span>
            </Link>

            {isAuthenticated && user?.role === 'admin' && (
              <Link 
                to="/admin" 
                className={`flex items-center space-x-2 text-sm font-medium transition-colors hover:text-primary ${
                  isActivePath('/admin') ? 'text-primary' : 'text-muted-foreground'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>Admin</span>
              </Link>
            )}
          </div>

          {/* User Actions */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && user ? (
              <>
                {/* Admin Quick Actions */}
                {user.role === 'admin' && (
                  <div className="hidden lg:flex items-center space-x-2">
                    <Link to="/admin/documents">
                      <Button variant="ghost" size="sm">
                        <FileText className="w-4 h-4 mr-2" />
                        Documents
                      </Button>
                    </Link>
                    <Link to="/admin/users">
                      <Button variant="ghost" size="sm">
                        <Users className="w-4 h-4 mr-2" />
                        Users
                      </Button>
                    </Link>
                  </div>
                )}

                {/* User Menu */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="flex items-center space-x-2">
                      <User className="w-4 h-4" />
                      <span className="hidden sm:inline">{user.email}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium">{user.email}</p>
                        <p className="text-xs text-muted-foreground capitalize">
                          {user.role} Account
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    
                    <DropdownMenuItem asChild>
                      <Link to="/chat" className="flex items-center">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Research Chat
                      </Link>
                    </DropdownMenuItem>
                    
                    {user.role === 'admin' && (
                      <>
                        <DropdownMenuItem asChild>
                          <Link to="/admin" className="flex items-center">
                            <Settings className="w-4 h-4 mr-2" />
                            Admin Dashboard
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                          <Link to="/admin/documents" className="flex items-center">
                            <FileText className="w-4 h-4 mr-2" />
                            Manage Documents
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                          <Link to="/admin/users" className="flex items-center">
                            <Users className="w-4 h-4 mr-2" />
                            Manage Users
                          </Link>
                        </DropdownMenuItem>
                      </>
                    )}
                    
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost">Login</Button>
                </Link>
                <Link to="/register">
                  <Button>Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
};

export default Navigation;