import type { CSSProperties } from "react";
import { cn } from "./ui/utils";
import { Button } from "./ui/button";
import { User, Table, BarChart3, Activity, Database, Users, BookOpen, Settings, RefreshCw, LogOut } from "lucide-react";
import logo from "figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png";
import { useAuth } from "../context/AuthContext";
import type { ViewType } from "../context/AppContext";
import { canAccessView } from "../lib/access";

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  className?: string;
}

export function Sidebar({ currentView, onViewChange, className }: SidebarProps) {
  const { user, logout } = useAuth();

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.username?.slice(0, 2).toUpperCase() ?? '??';

  const displayName = user?.full_name || user?.username || 'User';

  const navigationItems = [
    {
      id: "welcome" as ViewType,
      label: "Welcome",
      icon: Database,
      description: "Platform overview & features"
    },
    {
      id: "patient" as ViewType,
      label: "Patient Profile",
      icon: User,
      description: "Individual patient view"
    },
    {
      id: "registry" as ViewType,
      label: "Patient Registry",
      icon: Table,
      description: "All patients table view"
    },
    {
      id: "cohort" as ViewType,
      label: "Cohort Builder",
      icon: Users,
      description: "Advanced patient selection"
    },
    {
      id: "analytics" as ViewType,
      label: "Registry Analytics", 
      icon: BarChart3,
      description: "Data visualization & insights"
    },
    {
      id: "charts" as ViewType,
      label: "Chart Builder",
      icon: Activity,
      description: "Create custom visualizations"
    },
    {
      id: "etl" as ViewType,
      label: "ETL Monitor",
      icon: RefreshCw,
      description: "Track ETL runs and status"
    },
    {
      id: "dictionary" as ViewType,
      label: "Data Dictionary",
      icon: BookOpen,
      description: "Variables & metadata"
    }
  ].filter((item) => canAccessView(user, item.id as never));

  return (
    <div className={cn("app-sidebar-shell w-64 border-r border-sidebar-border bg-sidebar flex h-screen flex-col", className)}>
      <div className="app-sidebar-brand p-6 flex-shrink-0">
        <div className="flex items-center space-x-3">
          <img 
            src={logo} 
            alt="Magdi Yacoub Heart Foundation" 
            className="h-10 w-auto"
          />
          <div>
            <h2 className="text-lg font-medium text-sidebar-foreground">MYF Biolink</h2>
            <p className="text-xs text-sidebar-foreground/60">Heart Foundation Registry</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6">
        <nav className="space-y-2">
          {navigationItems.map((item, index) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            
            return (
              <Button
                key={item.id}
                data-active={isActive ? "true" : "false"}
                variant={isActive ? "default" : "ghost"}
                size="sm"
                className={cn(
                  "nav-item-button w-full justify-start h-auto p-3",
                  isActive 
                    ? "bg-sidebar-primary text-sidebar-primary-foreground" 
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
                style={{ "--stagger-index": index + 1 } as CSSProperties}
                onClick={() => onViewChange(item.id)}
              >
                <div className="flex items-start space-x-3 w-full">
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <div className="flex-1 text-left min-w-0">
                    <span className="text-sm block leading-tight">{item.label}</span>
                    <p className={cn(
                      "text-xs mt-1 whitespace-normal leading-relaxed",
                      isActive 
                        ? "text-sidebar-primary-foreground/80" 
                        : "text-sidebar-foreground/60"
                    )}>
                      {item.description}
                    </p>
                  </div>
                </div>
              </Button>
            );
          })}
        </nav>
      </div>
      
      <div className="p-6 border-t border-sidebar-border flex-shrink-0">
        <button 
          className="profile-card mb-4 w-full rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-3 text-left transition-colors hover:bg-sidebar-accent"
          onClick={() => onViewChange('profile')}
        >
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#00a2ddff] to-[#efb01bff] flex items-center justify-center text-white font-medium flex-shrink-0">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">{displayName}</p>
              <p className="text-xs text-sidebar-foreground/60 capitalize">{user?.role || 'User'}</p>
            </div>
          </div>
        </button>

        <div className="flex gap-2 mb-4">
          {canAccessView(user, 'settings') ? (
            <Button 
              variant="ghost" 
              size="sm" 
              className="flex-1 justify-start"
              onClick={() => onViewChange('settings')}
            >
              <Settings className="h-4 w-4 mr-2" />
              <span className="text-sm">Settings</span>
            </Button>
          ) : null}
          <Button
            variant="ghost"
            size="sm"
            className="justify-center text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={logout}
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="text-xs text-sidebar-foreground/60 space-y-1">
          <p>Registry Version 2.1.0</p>
          <p>Last Updated: Dec 2024</p>
          <p>Data Refresh: Live</p>
        </div>
      </div>
    </div>
  );
}