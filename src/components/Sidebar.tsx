import { cn } from "./ui/utils";
import { Button } from "./ui/button";
import { User, Table, BarChart3, Activity, Database, Users, BookOpen, Settings } from "lucide-react";
import logo from "figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png";

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  className?: string;
}

export function Sidebar({ currentView, onViewChange, className }: SidebarProps) {
  const navigationItems = [
    {
      id: "welcome",
      label: "Welcome",
      icon: Database,
      description: "Platform overview & features"
    },
    {
      id: "patient",
      label: "Patient Profile",
      icon: User,
      description: "Individual patient view"
    },
    {
      id: "registry",
      label: "Patient Registry",
      icon: Table,
      description: "All patients table view"
    },
    {
      id: "cohort",
      label: "Cohort Builder",
      icon: Users,
      description: "Advanced patient selection"
    },
    {
      id: "analytics",
      label: "Registry Analytics", 
      icon: BarChart3,
      description: "Data visualization & insights"
    },
    {
      id: "charts",
      label: "Chart Builder",
      icon: Activity,
      description: "Create custom visualizations"
    },
    {
      id: "dictionary",
      label: "Data Dictionary",
      icon: BookOpen,
      description: "Variables & metadata"
    }
  ];

  return (
    <div className={cn("w-64 bg-sidebar border-r border-sidebar-border flex flex-col h-screen", className)}>
      <div className="p-6 flex-shrink-0">
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
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            
            return (
              <Button
                key={item.id}
                variant={isActive ? "default" : "ghost"}
                size="sm"
                className={cn(
                  "w-full justify-start h-auto p-3",
                  isActive 
                    ? "bg-sidebar-primary text-sidebar-primary-foreground" 
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
                onClick={() => onViewChange(item.id)}
              >
                <div className="flex items-center space-x-3 w-full">
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <div className="flex-1 text-left min-w-0">
                    <span className="text-sm truncate block">{item.label}</span>
                    <p className={cn(
                      "text-xs mt-1 truncate",
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
          className="mb-4 p-3 rounded-lg bg-sidebar-accent/50 border border-sidebar-border w-full text-left hover:bg-sidebar-accent transition-colors"
          onClick={() => onViewChange('profile')}
        >
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#00a2ddff] to-[#efb01bff] flex items-center justify-center text-white font-medium flex-shrink-0">
              DR
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">Dr. Ahmed Hassan</p>
              <p className="text-xs text-sidebar-foreground/60">View Profile</p>
            </div>
          </div>
        </button>

        <Button 
          variant="ghost" 
          size="sm" 
          className="w-full justify-start mb-4"
          onClick={() => onViewChange('settings')}
        >
          <Settings className="h-4 w-4 mr-3" />
          <span className="text-sm">Settings</span>
        </Button>
        
        <div className="text-xs text-sidebar-foreground/60 space-y-1">
          <p>Registry Version 2.1.0</p>
          <p>Last Updated: Dec 2024</p>
          <p>Data Refresh: Live</p>
        </div>
      </div>
    </div>
  );
}